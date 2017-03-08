import json
import unittest
from dipla.discovery_server.app import DiscoveryServer, DiscoveryAddServerView
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

    def test_add_server_with_missing_details_fails(self):
        response = self.app.post("/add_server", data=dict(
            address="nope"))
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertIn("400", data["error"])

    def test_add_duplicate_server_fails(self):
        proj = Project("http://nope.com:4848", "Nope", "More Nope")
        self.servers[proj.address] = proj
        response = self.app.post("/add_server", data=dict(
            address=proj.address,
            title=proj.title,
            description=proj.description))
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertIn("409", data["error"])

    def test_valid_server_addresses_are_recognised(self):
        add_server_view = DiscoveryAddServerView({})
        check = add_server_view._is_valid_address
        self.assertTrue(check("https://disco.server.com:1972"))
        self.assertTrue(check("http://localhost:1482"))
        self.assertFalse(check("hi"))
        self.assertFalse(check("dipla.biz"))
        self.assertFalse(check("http://dcu.ie/registry"))
        self.assertFalse(check("meme.gold:1972"))

    def test_adding_bad_address_fails(self):
        response = self.app.post("/add_server", data=dict(
            address="hej!",
            title="praise switzerland",
            description="alt-norway's favourite server"))
        data = json.loads(response.data.decode())
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertIn("400", data["error"])


if __name__ == '__main__':
    unittest.main()
