from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.server import BinaryManager
from dipla.server.task_queue import TaskQueue, Task, DataSource
from dipla.shared import uid_generator

class Dipla:

    binary_mananger = BinaryManager()
    task_queue = TaskQueue()

    @staticmethod
    def distribute(function):
        base64_binary = get_encoded_script(function)
        #Dipla.binary_mananger.add_platform('.*', )

    @staticmethod
    def data_source(function):
        pass

    @staticmethod
    def start():
        # Start the dipla server
        pass

    def read_data_source(source):
        uid = uid_generator.generate_uid(length=8, existing_uids=[])
        # The Task name is never used so it is just set to 'input'
        read_task = Task(uid, 'input') 
        read_task.add_data_source(DataSource.create_source_from_iterable(source))
        task_queue.push_task(read_task)
        return Promise(uid)


class Promise:

    def __init__(self, promise_uid):
        self.uid = promise_uid
