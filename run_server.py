import sys

from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task, DataSource
from dipla.shared import uid_generator

def generate_uid(existing):
    return uid_generator.generate_uid(
        length = 8, existing_uids=existing)

def main(argv):
    tq = TaskQueue()
    
    root_source = [1, 2, 3, 4, 5]
    def consuming_read_function(stream, stream_location):
        values = list(stream)[stream_location:]
        stream.clear()
        return values

    # I know there's lots of generating ids here which will probably
    # annoy people. This will not be necessary in future code because
    # we will have a more sophisticated generation approach. The id
    # generation should not be done inside the Task constructor or
    # inside the add_data_source function

    # Create the fibonacci task depending on root_source
    fibonacci_task_uid = generate_uid(existing=[]) 
    fibonacci_task = Task(fibonacci_task_uid, 'fibonacci')
    
    iterable_source_uid1 = generate_uid(existing=[])
    fibonacci_task.add_data_source(DataSource.create_source_from_iterable(
        root_source, iterable_source_uid1))

    # Create the negate task depending on root_source
    negate_task_uid = generate_uid(existing=[fibonacci_task_uid])
    negate_task = Task(negate_task_uid, 'negate')

    iterable_source_uid2 = generate_uid(existing=[])
    negate_task.add_data_source(DataSource.create_source_from_iterable(
        root_source, iterable_source_uid2))

    # Create the reduce task depending on the first two tasks
    reduce_task_uid = generate_uid(
        existing=[fibonacci_task_uid, negate_task_uid])
    reduce_task = Task(reduce_task_uid, 'reduce')
    
    fibonacci_task_source_uid = generate_uid(existing=[])
    reduce_task.add_data_source(DataSource.create_source_from_task(
        fibonacci_task, fibonacci_task_source_uid, consuming_read_function))
    
    negate_task_source_uid = generate_uid(existing=[fibonacci_task_source_uid])
    reduce_task.add_data_source(DataSource.create_source_from_task(
        negate_task, negate_task_source_uid, consuming_read_function))


    tq.push_task(fibonacci_task)
    tq.push_task(negate_task)
    tq.push_task(reduce_task)

    bm = BinaryManager()
    bm.add_binary_paths('.*x.*', [
        ('fibonacci', 'fibonacci'),
        ('negate', 'negate'),
        ('reduce', 'reduce')
    ])
    bm.add_binary_paths('.*win32.*', [
        ('add', '/win32/add/path'),
        ('sub', '/win32/sub/path'),
    ])

    s = Server(tq, bm)
    print('Starting server')
    address, port = 'localhost', 8765
    if len(argv) > 1:
        if ':' in argv[1]:
            address, port = argv[1].split(':')
            port = int(port)
        else:
            address = argv[1]
    s.start(address, port)

if __name__ == '__main__':
    main(sys.argv)
