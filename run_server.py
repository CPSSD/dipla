from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task
from dipla.shared import uid_generator

def distributable_squarer(value):
    return value**2

def main():
    tq = TaskQueue()
    
    task_uid = uid_generator.generate_uid(
        length = 8, existing_uids=[])
    source = [1, 2, 3, 4, 5]

    tq.push_task(Task(task_uid, source, 'fibonacci'))

    bm = BinaryManager()
    bm.add_platform('.*ix.*', [
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
