""" Worker Group

A representation of a group of workers, which is used to manage the
order in which workers are chosen. This should track which workers are
available to start a new task, and which are currently running a task
"""

import heapq
import random
import operator

from functools import reduce


class WorkerGroup:

    # TODO(StefanKennedy): Add functionality to choose another
    # worker when a busy worker disconnects

    def __init__(self):
        # Ready Workers is a min heap, used to quickly find the most
        # preferrable worker during worker-leasing behaviour
        self.ready_workers = []
        self.busy_workers = {}

    def add_worker(self, worker):
        if worker.uid in self.worker_uids():
            raise ValueError("Unique ID " + worker.uid + " is already in use")
        heapq.heappush(self.ready_workers, worker)

    def remove_worker(self, uid):
        if uid in self.busy_workers:
            self.busy_workers.pop(uid)
            return

        for i in range(len(self.ready_workers)):
            if self.ready_workers[i].uid == uid:
                self.ready_workers.pop(i)
                heapq.heapify(self.ready_workers)
                return

        raise KeyError("No worker was found with the ID: " + uid)

    # Choose a worker to mark leased, so that this will not be used by
    # another task at the same time. This must be returned later using
    # return_worker so that the worker can be reused
    def lease_worker(self):
        if len(self.ready_workers) == 0:
            raise IndexError("No workers available to lease")
        chosen = heapq.heappop(self.ready_workers)
        self.busy_workers[chosen.uid] = chosen
        return chosen

    # Indicate that a leased worker is no longer needed and can now be
    # used by other tasks.
    def return_worker(self, uid):
        if uid not in self.busy_workers.keys():
            raise KeyError("No busy workers with the provided key")
        worker = self.busy_workers.pop(uid)
        heapq.heappush(self.ready_workers, worker)

    def worker_uids(self):
        return [x.uid for x in self._all_workers()]

    def _all_workers(self):
        return self.ready_workers + list(self.busy_workers.values())

    def generate_uid(self, length, safe=True,
                     choices='abcdefghijklmnopqrstuvwxyz'):
        worker_uids = self.worker_uids()

        # Remove duplicates from the choices string
        choices = ''.join(set(choices))

        # If safe mode is activated, raise an error if it is possible
        # that this search for a uid could run infintitely because
        # there are no unique IDs left to generate
        if safe and len(worker_uids) == len(choices)**length:
            raise WorkerIDsExhausted("""Safe mode active and it is
                possible that all UIDs have been exhausted""")

        def get_random_uid():
            return ''.join(random.choice(choices) for i in range(length))

        suggested_uid = get_random_uid()
        while suggested_uid in worker_uids:
            suggested_uid = get_random_uid()

        return suggested_uid


class WorkerIDsExhausted(Exception):
    pass


# Abstraction of the information necessary to represent a Worker in the
# worker group
class Worker:

    def __init__(self, uid, websocket, quality):
        """
        uid is the workers Unique Identifier string

        websocket is the workers connected websocket

        quality is a numeric indicator of how preferrable this worker is
        for running a task. This could depend on the hosts ping,
        reliability, processing power, etc.
        """
        self.uid = uid
        self._quality = quality
        self.websocket = websocket

    # The closer to zero the quality value is, the more preferable the
    # worker is
    def quality(self):
        # Squaring the values here is a placeholder until a more
        # relevant quality formula is determined
        return self._quality*self._quality

    def __eq__(self, other):
        return self.quality() == other.quality()

    def __gt__(self, other):
        return self.quality() > other.quality()
