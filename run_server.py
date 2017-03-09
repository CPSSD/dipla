from argparse import ArgumentParser
from logging import FileHandler
from queue import Queue
from random import random
from dipla.server.server import BinaryManager, Server, ServerEventListener
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator
from dipla.shared.logutils import LogUtils
from dipla.shared.statistics import StatisticsUpdater
from dipla.server.task_distribution import TaskInputDistributor
from dipla.server.task_distribution import VerificationInputStorer
from dipla.server.worker_group import WorkerGroup
from dipla.shared.network.server_connection_provider import \
    ServerConnectionProvider


def main():
    LogUtils.init(handler=FileHandler("DIPLA_SERVER.log"))

    args = get_arguments()

    task_queue = TaskQueue()
    add_tasks_to(task_queue)

    binary_manager = BinaryManager()
    add_binary_paths_to(binary_manager)

    statistics = generate_default_statistics()
    statistics_updater = StatisticsUpdater(statistics)

    established_connections = Queue()
    connection_provider = ServerConnectionProvider(
        established_connections,
        args.port,
        ServerEventListener
    )

    worker_group = WorkerGroup(statistics_updater)

    verification_inputs = {}
    verification_probability = 0.5
    verification_input_storer = VerificationInputStorer(
        verification_inputs,
        verification_probability,
        random
    )

    task_input_distributor = TaskInputDistributor(
        worker_group,
        task_queue,
        verification_input_storer
    )

    server = Server(
        connection_provider,
        task_queue,
        task_input_distributor
    )

    server.start()


def get_arguments():
    parser = ArgumentParser(description="Start a Dipla server.")
    parser.add_argument('-u', default='localhost', dest='url')
    parser.add_argument('-p', default=8765, dest='port', type=int)
    parser.add_argument('--pass', default=None, dest='password')
    return parser.parse_args()


def add_tasks_to(task_queue):
    server_side_task_uid = generate_uid(existing=[])
    server_side_task = Task(
        server_side_task_uid,
        'server_side',
        MachineType.server
    )
    root_source = [1, 2, 3, 4, 5]
    iterable_source_uid1 = generate_uid(existing=[])
    server_side_task.add_data_source(
        DataSource.create_source_from_iterable(
            root_source,
            iterable_source_uid1,
        )
    )
    fibonacci_task_uid = generate_uid(existing=[server_side_task_uid])
    fibonacci_task = Task(
        fibonacci_task_uid,
        'fibonacci',
        MachineType.client
    )
    server_side_source_uid = generate_uid(existing=[])
    fibonacci_task.add_data_source(
        DataSource.create_source_from_task(
            server_side_task,
            server_side_source_uid
        )
    )
    negate_task_uid = generate_uid(
        existing=[
            fibonacci_task_uid,
            server_side_task_uid
        ]
    )
    negate_task = Task(
        negate_task_uid,
        'negate',
        MachineType.client
    )
    iterable_source_uid2 = generate_uid(existing=[])
    negate_task.add_data_source(
        DataSource.create_source_from_iterable(
            root_source,
            iterable_source_uid2
        )
    )
    reduce_task_uid = generate_uid(
        existing=[
            fibonacci_task_uid,
            negate_task_uid,
            server_side_task_uid
        ]
    )
    reduce_task = Task(
        reduce_task_uid,
        'reduce',
        MachineType.client
    )

    def consuming_read_function(stream, stream_location):
        values = list(stream)[stream_location:]
        stream.clear()
        return values

    fibonacci_task_source_uid = generate_uid(existing=[])
    reduce_task.add_data_source(
        DataSource.create_source_from_task(
            fibonacci_task,
            fibonacci_task_source_uid,
            consuming_read_function
        )
    )
    negate_task_source_uid = generate_uid(existing=[fibonacci_task_source_uid])
    reduce_task.add_data_source(
        DataSource.create_source_from_task(
            negate_task,
            negate_task_source_uid,
            consuming_read_function
        )
    )

    tasks = [
        server_side_task,
        fibonacci_task,
        negate_task,
        reduce_task
    ]
    for task in tasks:
        task_queue.push_task(task)


def generate_default_statistics():
    return {
        'num_total_workers': 0,
        'num_idle_workers': 0,
    }


def generate_uid(existing):
    return uid_generator.generate_uid(
        length=8, existing_uids=existing)


def add_binary_paths_to(binary_manager):
    binary_manager.add_binary_paths('.*x.*', [
        ('fibonacci', 'fibonacci'),
        ('negate', 'negate'),
        ('reduce', 'reduce')
    ])
    binary_manager.add_binary_paths('.*win32.*', [
        ('fibonacci', 'fibonacci'),
        ('negate', 'negate'),
        ('reduce', 'reduce')
    ])


if __name__ == '__main__':
    main()
