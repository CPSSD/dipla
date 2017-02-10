import sys
import argparse

from dipla.server.server import BinaryManager, Server, ServerServices
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator
from dipla.api import Dipla


def generate_uid(existing):
    return uid_generator.generate_uid(
        length=8, existing_uids=existing)


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

    serverside_task_uid = generate_uid(existing=[])
    serverside_task = Task(
        serverside_task_uid, 'serverside', MachineType.server)

    iterable_source_uid1 = generate_uid(existing=[])
    serverside_task.add_data_source(DataSource.create_source_from_iterable(
        root_source, iterable_source_uid1))

    # Create the fibonacci task depending on root_source
    fibonacci_task_uid = generate_uid(existing=[serverside_task_uid])
    fibonacci_task = Task(fibonacci_task_uid, 'fibonacci', MachineType.client)

    serverside_source_uid = generate_uid(existing=[])
    fibonacci_task.add_data_source(DataSource.create_source_from_task(
        serverside_task, serverside_source_uid))

    # Create the negate task depending on root_source
    negate_task_uid = generate_uid(
        existing=[fibonacci_task_uid, serverside_task_uid])
    negate_task = Task(negate_task_uid, 'negate', MachineType.client)

    iterable_source_uid2 = generate_uid(existing=[])
    negate_task.add_data_source(DataSource.create_source_from_iterable(
        root_source, iterable_source_uid2))

    # Create the reduce task depending on the first two tasks
    reduce_task_uid = generate_uid(
        existing=[fibonacci_task_uid, negate_task_uid, serverside_task_uid])
    reduce_task = Task(reduce_task_uid, 'reduce', MachineType.client)

    fibonacci_task_source_uid = generate_uid(existing=[])
    reduce_task.add_data_source(DataSource.create_source_from_task(
        fibonacci_task, fibonacci_task_source_uid, consuming_read_function))

    negate_task_source_uid = generate_uid(existing=[fibonacci_task_source_uid])
    reduce_task.add_data_source(DataSource.create_source_from_task(
        negate_task, negate_task_source_uid, consuming_read_function))

    tq.push_task(serverside_task)
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
        ('fibonacci', 'fibonacci'),
        ('negate', 'negate'),
        ('reduce', 'reduce')
    ])

    s = Server(tq, ServerServices(bm))
    print('Starting server')
    parser = argparse.ArgumentParser(description="Start a Dipla server.")
    parser.add_argument('-u', default='localhost', dest='url')
    parser.add_argument('-p', default=8765, dest='port', type=int)
    parser.add_argument('--pass', default=None, dest='password')
    args = parser.parse_args()
    s.start(args.url, args.port, args.password)

if __name__ == '__main__':
    main(sys.argv)
