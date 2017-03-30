import asyncio
import os
import threading
import time
import websockets
import werkzeug
from flask import abort, Flask, json, request
from flask.views import View, MethodView
from dipla.discovery_server.project import Project
from threading import Lock


class DiscoveryGetServersView(View):

    def __init__(self, servers, servers_lock):
        self.__servers = servers
        self.__servers_lock = servers_lock

    def dispatch_request(self, *url_args, **url_kwargs):
        server_list = []
        with self.__servers_lock:
            for key in self.__servers:
                server = self.__servers[key]
                if not server.alive:
                    continue
                server_list.append({
                    'address': server.address,
                    'title': server.title,
                    'description': server.description,
                })
        return json.jsonify({
            'success': True,
            'servers': server_list,
        })


class DiscoveryAddServerView(MethodView):

    def __init__(self, servers, servers_lock, server_file=None):
        self.__servers = servers
        self.__servers_lock = servers_lock
        self.__server_file = server_file

    def _is_valid_address(self, address):
        """Make sure that the given address includes both a protocol
        (eg. http or https) and a port."""
        return address.count(':') == 2

    def _write_new_project_to_file(self, project):
        with open(self.__server_file, 'a') as f:
            s = json.dumps(project,
                           default=lambda x: x.serialize(),
                           indent=None)
            f.write(s)
            f.write('\n')

    def post(self):
        if not self._is_valid_address(request.form['address']):
            abort(400)
        project = Project(request.form['address'],
                          request.form['title'],
                          request.form['description'],
                          alive=True)
        with self.__servers_lock:
            if project.address in self.__servers.keys():
                abort(409)
            self.__servers[project.address] = project
        if self.__server_file is not None:
            self._write_new_project_to_file(project)
        return json.jsonify({
            'success': True,
        })

class ProjectStatusChecker(threading.Thread):

    def __init__(self, servers, servers_lock, poll_time=10):
        """Create a new ProjectStatusChecker. This is a loop that
        runs in a new thread, activated by .start(). It runs through
        all of the projects the discovery server knows about,
        and checks if each is alive and accepting connections. It
        also does one initial run-through when it is first started,
        with no pauses between checks, as the directory server
        might have loaded some old information from a file that
        needs to be updated.

        Params:
        - servers: A reference to the dict of projects the directory
          server keeps.
        - servers_lock: A reference to the mutex controlling access
          to the project dict.
        - poll_time: An int defining the number of seconds to wait
          between each project check. Defaults to 10 seconds."""
        super().__init__()
        self.__servers = servers
        self.__servers_lock = servers_lock
        self.__poll_time = poll_time

    async def _websocket_connect(self, address):
        try:
            message = await websockets.connect(address)
            return message
        except Exception as e:
            return None

    def _check_project(self, project):
        """Return True if a websocket connection to the given
        project is accepted, and False oherwise."""
        loop = asyncio.get_event_loop()
        websocket = loop.run_until_complete(
                self._websocket_connect(project.address))
        return websocket is not None

    def _check_all_projects(self, timeout, repeat=False):
        """Run through all projects and update their entries
        in the server dict to reflect whether they are alive
        and accepting connections or not. Wait `timeout`
        seconds between each project check."""
        i = 0
        while True:
            with self.__servers_lock:
                if not repeat and i >= len(self.__servers):
                    break
                if len(self.__servers) > 0:
                    keys = sorted(list(self.__servers.keys()))
                    i %= len(keys)
                    k = keys[i]
                    proj = self.__servers[k]
                    alive = self._check_project(proj)
                    print('Project', proj.address, 'alive:', alive)
                    self.__servers[k].alive = alive
            time.sleep(timeout)
            i += 1

    def run(self):
        # this runs in a new thread, so we need a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # run through all projects first to see what is still
        # online out of all of the servers loaded from file
        self._check_all_projects(0)
        # continually run through servers with a timeout,
        # to keep the server list up to date
        self._check_all_projects(self.__poll_time, repeat=True)


class DiscoveryServer:

    def __init__(self, host='0.0.0.0', port=8766, server_file=None):
        """
        Start a discovery server running.

        Params:
        - host: A string with the host that this server will run on.
          Defaults to '0.0.0.0', which will accept incoming
          connections on all IPs.
        - port: An integer with the port this server will run on.
        - server_file: A string declaring the path of a file to
          save project details to as new projects announce themselves.
          When the server boots, it will load project information
          from this file to pre-populate its project listing. If the
          given file doesn't exist, it will be created. Defaults to
          None, which means no file will be used to pre-populate
          the server, and the new projects it finds out about will
          not be saved anywhere.
        """
        self.__host = host
        self.__port = port
        self._servers = {}
        self.__server_file = server_file

        if server_file is not None:
            def opener(path, flags):
                # define opener that will open the file for reading
                # and create the file if it doesn't already exist
                return os.open(path, os.O_CREAT | os.O_RDONLY)

            with open(server_file, opener=opener) as f:
                lines = f.readlines()
                for line in lines:
                    data = json.loads(line)
                    project = Project(data['address'],
                                      data['title'],
                                      data['description'],
                                      alive=False)
                    self._servers[project.address] = project

        self.__servers_lock = Lock()
        self._status_checker = ProjectStatusChecker(
                self._servers,
                self.__servers_lock)
        self._app = self._create_flask_app()

    def _create_flask_app(self):
        """Create the flask app and register the endpoints,
        but don't run it yet."""
        app = Flask(__name__)
        get_servers = DiscoveryGetServersView.as_view(
            "api/get_servers",
            servers=self._servers,
            servers_lock=self.__servers_lock)
        add_server = DiscoveryAddServerView.as_view(
            "api/add_server",
            servers=self._servers,
            servers_lock=self.__servers_lock,
            server_file=self.__server_file)
        app.add_url_rule("/get_servers", "api/get_servers",
                         view_func=get_servers)
        app.add_url_rule("/add_server", "api/add_server",
                         view_func=add_server)
        app.register_error_handler(
            werkzeug.exceptions.BadRequest, self._error_bad_request)
        app.register_error_handler(
            werkzeug.exceptions.Conflict, self._error_conflict)
        return app

    def _error_bad_request(self, e):
        return json.jsonify({
            'success': False,
            'error': '400: Bad Request',
        })

    def _error_conflict(self, e):
        return json.jsonify({
            'success': False,
            'error': '409: Conflict',
        })

    def start(self):
        self._status_checker.start()
        self._app.run(host=self.__host, port=self.__port)
