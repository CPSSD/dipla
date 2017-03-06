import werkzeug
from flask import abort, Flask, json
app = Flask(__name__)

servers = set()

def is_valid_address(address):
    return ':' in address

@app.route("/get_servers")
def get_servers():
    return json.jsonify({
        'success': True,
        'servers': list(servers),
    })

@app.route("/add_server/<string:address>")
def add_server(address):
    if not is_valid_address(address):
        abort(400)
    if address in servers:
        abort(409)
    servers.add(address)
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
