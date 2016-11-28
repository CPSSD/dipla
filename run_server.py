from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task
from dipla.shared import uid_generator

def distributable_squarer(value):
    return value**2

def main():
    tq = TaskQueue()
    
    first_task_uid = uid_generator.generate_uid(
        length = 8, existing_uids=[])
    second_task_uid = uid_generator.generate_uid(
        length = 8, existing_uids=[first_task_uid])
    source = [1, 2, 3, 4, 5]

    tq.push_task(Task(first_task_uid, source, 'fibonacci'))
    tq.push_task(
        Task(second_task_uid, source, 'fibonacci'),
        dependencies=[first_task_uid])

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
