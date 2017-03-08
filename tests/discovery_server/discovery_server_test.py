import json
import unittest
from dipla.discovery_server.app import DiscoveryServer
from dipla.discovery_server.project import Project


class DiscoveryTest(unittest.TestCase):

    def setUp(self):

        self.servers = {}
        self.discovery_server = DiscoveryServer(host='localhost',
                                                port=1337,
                                                servers=self.servers)
        self.app = self.discovery_server._app.test_client()

    def test_get_servers_empty(self):
        response = self.app.get("/get_servers")
        self.assertEqual("200 OK", response.status)
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("servers", data)
        self.assertEqual(0, len(data["servers"]))

    def test_get_servers_changed(self):
        response = self.app.get("/get_servers")
        data = json.loads(response.data.decode())
        self.assertEqual(0, len(data["servers"]))

        address = "http://example.com:1234"
        self.servers[address] = Project(address, None, None)
        response = self.app.get("/get_servers")
        data = json.loads(response.data.decode())
        self.assertEqual(1, len(data["servers"]))

    def test_add_server(self):
        self.assertEqual(0, len(self.servers))
        address = "http://socialism.software:666"
        response = self.app.post("/add_server", data=dict(
            address=address,
            title="Socialist Software",
            description="inset lenin meme here"))
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertEqual(1, len(self.servers))
        self.assertEqual(address, self.servers.popitem()[1].address)

    def test_add_bad_server_fails(self):
        response = self.app.post("/add_server", data=dict(
            address="nope"))
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertIn("400", data["error"])


if __name__ == '__main__':
    unittest.main()
