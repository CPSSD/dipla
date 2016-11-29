from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task, DataSource
from dipla.shared import uid_generator

def distributable_squarer(value):
    return value**2

def main():
    tq = TaskQueue()
    
    root_source = [1, 2, 3, 4, 5]

    # Create a first task that depends on root_source, a iterable
    # collection
    first_task_uid = uid_generator.generate_uid(
        length = 8, existing_uids=[])
    first_task = Task(first_task_uid, 'fibonacci')
    first_task.add_data_source(
        DataSource.create_source_from_iterable(root_source))

    # Create a second task that depends on the first task's output
    second_task_uid = uid_generator.generate_uid(
        length = 8, existing_uids=[first_task_uid])
    second_task = Task(second_task_uid, 'fibonacci')
    second_task.add_data_source(
        DataSource.create_source_from_task(first_task))

    tq.push_task(first_task)
    tq.push_task(second_task)

    bm = BinaryManager()
    bm.add_platform('.*x.*', [
        ('fibonacci', 'fibonacci')
    ])
    bm.add_platform('.*win32.*', [
        ('add', '/win32/add/path'),
        ('sub', '/win32/sub/path'),
    ])

    s = Server(tq, bm)
    print('Starting server')
    s.start()

if __name__ == '__main__':
    main()
