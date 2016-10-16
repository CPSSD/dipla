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
        self.workers[uid] = worker

    def remove_worker(self, uid):
        del self.workers[uid]

    def lease_worker(self):
        chosen = self.ready_workers.items[0]
        busy_workers[chosen[0]] = chosen[1]

    def return_worker(self, uid):
        worker = self.busy_workers.pop(uid)
        self.ready_worlers[uid] = worker
        
