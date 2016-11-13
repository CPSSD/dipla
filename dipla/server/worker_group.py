"""
This module contains the WorkerGroup and other supporting classes. It is
intended for this file to contain the code to manage the workers.
"""
import heapq
import random
import operator

from functools import reduce


class WorkerGroup:
    """
    A representation of a group of workers which is used to manage the
    order in which workers are chosen.

    This tracks which workers are available to start a new task, and which are
    currently running a task.
    """

    # TODO(StefanKennedy): Add functionality to choose another
    # worker when a busy worker disconnects

    def __init__(self):
        # Ready Workers is a min heap, used to quickly find the most
        # preferrable worker during worker-leasing behaviour
        self.ready_workers = []
        self.busy_workers = {}

    def add_worker(self, worker):
        """
        Add a worker to the group in the 'ready' state.

        Params:
         - worker: The Worker object to be added.

        Raises:
         - ValueError when a worker with the same uid already exists in the
           group.
        """
        if worker.uid in self.worker_uids():
            raise ValueError("Unique ID " + worker.uid + " is already in use")
        heapq.heappush(self.ready_workers, worker)

    def remove_worker(self, uid):
        """
        Removes a worker (identified by it's uid) from the group, irregardless
        of its state.

        Params:
         - uid: The unique ID of the worker to be removed.

        Raises:
         - KeyError if the uid provided does not match any of the workers in
           the group.
        """
        if uid in self.busy_workers:
            self.busy_workers.pop(uid)
            return

        for i in range(len(self.ready_workers)):
            if self.ready_workers[i].uid == uid:
                self.ready_workers.pop(i)
                heapq.heapify(self.ready_workers)
                return

        raise KeyError("No worker was found with the ID: " + uid)

    def lease_worker(self):
        """
        Choose a worker to mark leased so that this will not be used by another
        task at the same time. This must be returned later using return_worker
        so that the worker can be reused.

        Returns:
         - The highest quality available Worker
        """
        if len(self.ready_workers) == 0:
            raise IndexError("No workers available to lease")
        chosen = heapq.heappop(self.ready_workers)
        self.busy_workers[chosen.uid] = chosen
        return chosen

    def return_worker(self, uid):
        """
        Indicate that a leased Worker is no longer needed and can now be used
        by other tasks. The Worker object must not be used after it is
        returned.

        Params:
         - uid: The uid of the worker to be returned and marked as available

        Raises:
         - KeyError if the uid doesn't correspond to any leased workers
        """
        if uid not in self.busy_workers.keys():
            raise KeyError("No busy workers with the provided key")
        worker = self.busy_workers.pop(uid)
        heapq.heappush(self.ready_workers, worker)

    def worker_uids(self):
        """
        Returns:
         - The uids of all workers, regardless of state
        """
        return [x.uid for x in self._all_workers()]

    def _all_workers(self):
        """
        Returns:
         - A list of all the ready workers and busy workers
        """
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


        while True:
            suggested_uid = ''.join(
                    random.choice(choices) for i in range(length))
            if not suggested_uid in worker_uids:
                return suggested_uid


class WorkerIDsExhausted(Exception):
    pass


class Worker:
    """
    Abstraction of the information necessary to represent a worker in the
    WorkerGroup.
    """

    def __init__(self, uid, websocket, quality):
        """
        Initalises the worker.

        Params:
         - uid: The workers Unique Identifier string.
         - websocket: The workers connected websocket.
         - quality: A numeric indicator of how preferrable this worker is for
           running a task. This could depend on the hosts ping, reliability,
           processing power, etc.
        """
        self.uid = uid
        self._quality = quality
        self.websocket = websocket

    def quality(self):
        """
        Provides a value for the quality of the worker. The closer to 0 the
        value is, the more preferable the worker. This value may differ from
        what was provided in the constructor.

        Returns:
         - An integer 'quality' value.
        """
        # Squaring the values here is a placeholder until a more
        # relevant quality formula is determined
        return self._quality*self._quality

    def __eq__(self, other):
        return self.quality() == other.quality()

    def __gt__(self, other):
        return self.quality() > other.quality()
