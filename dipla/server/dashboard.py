from flask import Flask, Blueprint
from threading import Thread


index_page = Blueprint('index', __name__, template_folder='templates')

class DashboardServer(Thread):


    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    @index_page.route("/")
    def index():
        return "hi"

    def run(self):
        print('Running dashboard on {}:{}'.format(self.host, self.port))
        app = Flask(__name__)
        app.register_blueprint(index_page)
        app.run(host=self.host, port=self.port)
