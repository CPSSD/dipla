import os
import werkzeug
from flask import abort, Flask, json, request
from flask.views import View, MethodView
from dipla.discovery_server.project import Project


class DiscoveryGetServersView(View):

    def __init__(self, servers):
        self.__servers = servers

    def dispatch_request(self, *url_args, **url_kwargs):
        server_list = []
        for key in self.__servers:
            server = self.__servers[key]
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

    def __init__(self, servers, server_file=None):
        self.__servers = servers
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
                          request.form['description'])
        if project.address in self.__servers.keys():
            abort(409)
        self.__servers[project.address] = project
        if self.__server_file is not None:
            self._write_new_project_to_file(project)
        return json.jsonify({
            'success': True,
        })


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
                                      data['description'])
                    self._servers[project.address] = project

        self._app = self._create_flask_app()

    def _create_flask_app(self):
        """Create the flask app and register the endpoints,
        but don't run it yet."""
        app = Flask(__name__)
        get_servers = DiscoveryGetServersView.as_view(
            "api/get_servers", servers=self._servers)
        add_server = DiscoveryAddServerView.as_view(
            "api/add_server",
            servers=self._servers,
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
        self._app.run(host=self.__host, port=self.__port)
