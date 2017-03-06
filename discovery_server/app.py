from flask import Flask
app = Flask(__name__)

servers = set()

@app.route("/get_servers")
def get_servers():
    return str(servers)

@app.route("/add_server/<string:address>")
def add_server(address):
    servers.add(address)
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8766)
