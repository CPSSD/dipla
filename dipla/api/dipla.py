from dipla.server import task_queue
from dipla.server.task_queue import TaskQueue, Task
from dipla.shared import uid_generator

def read_data_source(source):
    uid = uid_generator.generate_uid(length=8, existing_uids=[])
    # The Task name is never used so it is just set to 'input'
    read_task = Task(uid, 'input') 
    read_task.add_data_source(DataSource.create_source_from_iterable(source))
    queue = TaskQueue()
    return Promise(uid, queue)


class Promise:

    def __init__(self, promise_uid, task_queue):
        self.uid = promise_uid
        self.task_queue = task_queue
