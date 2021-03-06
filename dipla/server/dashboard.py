import os
import subprocess
from dipla.environment import PROJECT_DIRECTORY
from flask import Flask, json, render_template
from flask.views import View
from threading import Thread


class DashboardView(View):
    """A superclass for the Views needed for the dashboard,
    to allow them to share a common constructor. This constructor
    is called whenever SomethingView.as_view is called, and all
    parameters should be passed then."""

    def __init__(self, stats):
        self.__stats = stats

    def _get_stat_json(self):
        return json.dumps(self.__stats.read_all())


class DashboardIndexView(DashboardView):
    """The view for the user-oriented index of the dashboard."""

    def dispatch_request(self, *url_args, **url_kwargs):
        return render_template("index.html", stats=self._get_stat_json())


class DashboardGetStatsView(DashboardView):
    """A view returning all of the stat data, in json format."""

    def dispatch_request(self, *url_args, **url_kwargs):
        return self._get_stat_json()


class DashboardServer(Thread):
    """A thin wrapper on a Flask server, allowing it to run in its
    own thread, and potentially allowing multiple instances to
    run. Per-instance data should be passed in to the constructor.

    If you want to run this server, you should use the .start() method
    that is inherited from threading.Thread. You should not use the
    .run() method specified here."""

    def __init__(self, host, port, stats):
        """Initialise the Dashboard Server.

        Params:
         - host: A string describing where the server will be run from.
         - port: An int saying which port to open for the server.
         - stats: An instance of shared.statistics.StatisticsReader.
        """
        super().__init__()
        self.__host = host
        self.__port = port
        self.__stats = stats
        # cannot be self.__app, as app needs to be accessed from tests
        self._app = self._create_flask_app()

    def _create_flask_app(self):
        """Create the base flask app, register all of the endpoints, but
        don't start it running yet."""
        static_folder = os.path.join(PROJECT_DIRECTORY, "dashboard", "static")
        template_folder = os.path.join(PROJECT_DIRECTORY,
                                       "dashboard",
                                       "templates")
        app = Flask(__name__,
                    static_folder=static_folder,
                    template_folder=template_folder)
        index = DashboardIndexView.as_view("index", stats=self.__stats)
        get_stats = DashboardGetStatsView.as_view("get_stats",
                                                  stats=self.__stats)
        app.add_url_rule("/", "index", view_func=index)
        app.add_url_rule("/get_stats", "get_stats", view_func=get_stats)
        return app

    def run(self):
        """Install javascript dependencies, and run the dashboard server.
        This should not be called directly, call the .start() method
        inherited from threading.Thread instead."""

        # install javascript dependencies. If they have already been
        # installed, this will only take a second, but it will take a
        # long time if they have not.
        proc = subprocess.Popen(["npm", "install"],
                                cwd=os.path.join(PROJECT_DIRECTORY,
                                                 "dashboard"))
        # Don't want to build project before we have the dependencies.
        proc.wait()

        # Transpile and pack the javascript. This will take 2-3 seconds.
        proc = subprocess.Popen(["npm", "run", "build"],
                                cwd=os.path.join(PROJECT_DIRECTORY,
                                                 "dashboard"))
        # Don't make the server live until all assets are ready.
        proc.wait()

        self._app.run(host=self.__host, port=self.__port)
