import json
import unittest
from dipla.server.dashboard import DashboardServer
from dipla.shared.statistics import StatisticsReader


class DashboardTest(unittest.TestCase):

    def setUp(self):

        self.stats = {"foo": "bar", "baz": 4}
        stat_reader = StatisticsReader(self.stats)
        self.dashboard = DashboardServer(host='localhost',
                                         port=1337,
                                         stats=stat_reader)
        self.app = self.dashboard.app.test_client()

    def test_index_template_loads(self):
        response = self.app.get("/")
        self.assertEqual("200 OK", response.status)
        raw_data = response.data.decode()
        self.assertIn("foo", raw_data)
        self.assertIn("bar", raw_data)
        self.assertIn("baz", raw_data)

    def test_static_file_loads(self):
        response = self.app.get("/static/style.css")
        self.assertEqual("200 OK", response.status)

    def test_get_stats_returns_correct_json(self):
        response = self.app.get("/get_stats")
        self.assertEqual("200 OK", response.status)
        raw_data = response.data.decode()
        parsed_data = json.loads(raw_data)
        self.assertEqual(2, len(parsed_data.keys()))
        self.assertEqual("bar", parsed_data["foo"])

        self.stats["foo"] = "quux"
        self.stats["bran"] = "don"
        response = self.app.get("/get_stats")
        raw_data = response.data.decode()
        parsed_data = json.loads(raw_data)
        self.assertEqual(3, len(parsed_data.keys()))
        self.assertEqual("quux", parsed_data["foo"])
        self.assertEqual("don", parsed_data["bran"])
