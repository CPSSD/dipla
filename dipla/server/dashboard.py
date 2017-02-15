from flask import Flask, Blueprint
from flask.views import View
from threading import Thread



class DashboardView(View):

    def __init__(self, stats):
        self.stats = stats

class DashboardIndexView(DashboardView):
    
    def dispatch_request(self, *url_args, **url_kwargs):
        return str(self.stats.read_all())

class DashboardGetStatsView(DashboardView):

    def dispatch_request(self, *url_args, **url_kwargs):
        return str(self.stats.read_all())

class DashboardServer(Thread):


    def __init__(self, host, port, stats):
        super().__init__()
        self.host = host
        self.port = port
        self.stats = stats

    def run(self):
        print('Running dashboard on {}:{}'.format(self.host, self.port))
        app = Flask(__name__)
        index = DashboardIndexView.as_view("index", stats=self.stats)
        get_stats = DashboardGetStatsView.as_view("get_stats",
                                                  stats=self.stats)
        app.add_url_rule("/", "index", view_func=index)
        app.add_url_rule("/get_stats", "get_stats", view_func=get_stats)
        app.run(host=self.host, port=self.port)
