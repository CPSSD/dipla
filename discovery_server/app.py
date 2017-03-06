import werkzeug
from flask import abort, Flask, json, request
from project import Project
app = Flask(__name__)

servers = {}

def is_valid_address(address):
    return ':' in address

@app.route("/get_servers")
def get_servers():
    server_list = []
    for key in servers:
        server = servers[key
        server_list.append({
            'address': server.address,
            'title': server.title,
            'description': server.description,
        })
    return json.jsonify({
        'success': True,
        'servers': server_list,
    })

@app.route("/add_server", methods=['POST'])
def add_server():
    if not is_valid_address(request.form['address']):
        abort(400)
    project = Project(request.form['address'],
                      request.form['title'],
                      request.form['description'])
    if project.address in servers.keys():
        abort(409)
    servers[project.address] = project
    return json.jsonify({
        'success': True,
    })

@app.errorhandler(werkzeug.exceptions.BadRequest)
def error_bad_request(e):
    return json.jsonify({
        'success': False,
        'error': '400: Bad Request',
    })

@app.errorhandler(werkzeug.exceptions.Conflict)
def error_conflict(e):
    return json.jsonify({
        'success': False,
        'error': '409: Conflict',
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8766)
