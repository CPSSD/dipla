""" Worker Group

A representation of a group of workers, which is used to manage the
order in which workers are chosen. This should track which workers are
available to start a new task, and which are currently running a task
"""


class WorkerGroup:
    
    def __init__(self):
        self.ready_workers = {}
        self.busy_workers = {}

    def add_worker(self, uid, worker):
        self.ready_workers[uid] = worker

    def remove_worker(self, uid):
        if(uid in self.ready_workers):
            del self.ready_workers[uid]
        else:
            del self.busy_workers[uid]

    def lease_worker(self):
        chosen = self.ready_workers.items[0]
        busy_workers[chosen[0]] = chosen[1]

    def return_worker(self, uid):
        worker = self.busy_workers.pop(uid)
        self.ready_workers[uid] = worker
        
    def worker_keys(self):
        return self.__all_workers().keys()

    def worker_sockets(self):
        return self.__all_workers().values()

    def __all_workers(self):
        return {**self.ready_workers, **self.busy_workers}
