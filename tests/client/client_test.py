import unittest
import json
from dipla.client.client import Client


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.client = Client('no address')

    def test_send(self):
        self.client.send({'label': 'test1', 'data': {}})
        self.assertFalse(self.client.queue.empty())
        s = self.client.queue.get()
        j = json.loads(s)
        self.assertEqual(j['label'], 'test1')
        self.assertEqual(j['data'], {})
        self.assertTrue(self.client.queue.empty())
