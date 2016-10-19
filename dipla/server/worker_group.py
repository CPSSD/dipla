""" Worker Group

A representation of a group of workers, which is used to manage the
order in which workers are chosen. This should track which workers are
available to start a new task, and which are currently running a task
"""

import heapq

class WorkerGroup:
    
    def __init__(self):
        self.ready_workers = []
        self.busy_workers = {}

    def add_worker(self, worker):
        if worker.uid in self.worker_uids():
            raise UniqueError("Unique ID " + worker.uid + " is already in use")
        heapq.heappush(self.ready_workers, worker)

    def remove_worker(self, uid):
        # TODO(StefanKennedy): Add functionality to choose another
        # worker when a busy worker disconnects
        if uid in self.busy_workers:
            del self.busy_workers[uid]
            return
        
        for i in range(0, len(self.ready_workers)):
            if self.ready_workers[i].uid == uid:
                self.ready_workers.pop(i)
                heapq.heapify(self.ready_workers)
                return 

        raise KeyError("No worker was found with the ID: " + uid)

    # Choose a worker to mark leased, so that this will not be used by
    # another task at the same time
    def lease_worker(self):
        if len(self.ready_workers) == 0:
            raise IndexError("No workers available to lease")
        chosen = heapq.heappop(self.ready_workers)
        self.busy_workers[chosen.uid] = chosen
        return chosen

    # Indicate that a leased worker is no longer needed and can now be
    # used by other tasks
    def return_worker(self, uid):
        if uid not in self.busy_workers.keys():
            raise KeyError("No busy workers with the provided key")
        worker = self.busy_workers.pop(uid)
        heapq.heappush(self.ready_workers, worker)
        
    def worker_uids(self):
        return [x.uid for x in self.__all_workers()]

    def __all_workers(self):
        return self.ready_workers + list(self.busy_workers.values())


# Abstraction of the information necessary to represent a Worker in the
# worker group
class Worker:
    
    def __init__(self, uid, quality, websocket):
        self.uid = uid
        self._quality = quality
        self.websocket = websocket

    # The closer to zero the quality value is, the more preferrable
    # the worker is
    def quality(self):
        return self._quality**2

    def __eq__(self, other):
        return self.quality() == other.quality()

    def __gt__(self, other):
        return self.quality() > other.quality()

# Error raised when a suggested value is not unique in a collection
class UniqueError(Exception):
    pass
