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
        heapq.heappush(self.ready_workers, worker)

    def remove_worker(self, uid):
        if(uid in self.busy_workers):
            del self.busy_workers[uid]
        else:
            for i in range(0, len(self.ready_workers)):
                if self.ready_workers[i].uid == uid:
                    self.ready_workers.pop(i)
                    break
            heapq.heapify(self.ready_workers)

    def lease_worker(self):
        if len(self.ready_workers) == 0:
            raise IndexError("No workers available to lease")
        chosen = heapq.heappop(self.ready_workers)
        self.busy_workers[chosen.uid] = chosen
        return chosen

    def return_worker(self, uid):
        if uid not in self.busy_workers.keys():
            raise KeyError("No busy workers with the provided key")
        worker = self.busy_workers.pop(uid)
        heapq.heappush(self.ready_workers, worker)
        
    def worker_uids(self):
        return [x.uid for x in self.__all_workers()]

    def worker_sockets(self):
        return [w.websocket for w in self.__all_workers().values()]

    def __all_workers(self):
        return self.ready_workers + list(self.busy_workers.values())


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
