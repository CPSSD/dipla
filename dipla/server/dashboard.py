import os
from dipla.environment import PROJECT_DIRECTORY
from flask import Flask, Blueprint, json, render_template
from flask.views import View
from threading import Thread


class DashboardView(View):
    """A superclass for the Views needed for the dashboard,
    to allow them to share a common constructor. This constructor
    is called whenever SomethingView.as_view is called, and all
    parameters should be passed then."""

    def __init__(self, stats):
        self.stats = stats


class DashboardIndexView(DashboardView):
    """The view for the user-oriented index of the dashboard."""

    def dispatch_request(self, *url_args, **url_kwargs):
        return render_template("index.html")
        return str(self.stats.read_all())


class DashboardGetStatsView(DashboardView):
    """A view returning all of the stat data, in json format."""

    def dispatch_request(self, *url_args, **url_kwargs):
        return str(json.dumps(self.stats.read_all(), indent=4))


class DashboardServer(Thread):
    """A thin wrapper on a Flask server, allowing it to run in its
    own thread, and potentially allowing multiple instances to
    run. Per-instance data should be passed in to the constructor."""

    def __init__(self, host, port, stats):
        super().__init__()
        self.host = host
        self.port = port
        self.stats = stats

    def run(self):
        print('Running dashboard on {}:{}'.format(self.host, self.port))
        static_folder = os.path.join(PROJECT_DIRECTORY, "dashboard", "static")
        template_folder = os.path.join(PROJECT_DIRECTORY, "dashboard", "templates")
        print(static_folder)
        app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
        index = DashboardIndexView.as_view("index", stats=self.stats)
        get_stats = DashboardGetStatsView.as_view("get_stats",
                                                  stats=self.stats)
        static_files = Blueprint("static files", __name__,
                                 template_folder="templates")
        app.add_url_rule("/", "index", view_func=index)
        app.add_url_rule("/get_stats", "get_stats", view_func=get_stats)
        app.run(host=self.host, port=self.port)
