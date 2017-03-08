import werkzeug
from flask import abort, Flask, json, request
from flask.views import View, MethodView
from project import Project


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

    def __init__(self, servers):
        self.__servers = servers

    def _is_valid_address(self, address):
        return ':' in address

    def post(self):
        if not self._is_valid_address(request.form['address']):
            abort(400)
        project = Project(request.form['address'],
                          request.form['title'],
                          request.form['description'])
        if project.address in self.__servers.keys():
            abort(409)
        self.__servers[project.address] = project
        return json.jsonify({
            'success': True,
        })


class DiscoveryServer:

    def __init__(self, host='0.0.0.0', port=8766, servers=None):
        self.__host = host
        self.__port = port
        if servers is None:
            self.__servers = {}
        else:
            self.__servers = servers
        self._app = self._create_flask_app()

    def _create_flask_app(self):
        """Create the flask app and register the endpoints, but don't run it yet."""
        app = Flask(__name__)
        get_servers = DiscoveryGetServersView.as_view("api/get_servers", servers = self.__servers)
        add_server = DiscoveryAddServerView.as_view("api/add_server", servers = self.__servers)
        app.add_url_rule("/get_servers", "api/get_servers", view_func = get_servers)
        app.add_url_rule("/add_server", "api/add_server", view_func = add_server)
        app.register_error_handler(werkzeug.exceptions.BadRequest, self._error_bad_request)
        app.register_error_handler(werkzeug.exceptions.Conflict, self._error_conflict)
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


if __name__ == '__main__':
    server = DiscoveryServer()
    server.start()
