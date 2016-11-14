from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task


def main():
    tq = TaskQueue()
    tasks = [
        ('1 2', 'add'),
        ('32 4', 'add'),
        ('16 4', 'sub'),
    ]
    for data, label in tasks:
        tq.push_task(Task(data, label))
        print('Added data "' + data + '" for task', label)

    bm = BinaryManager()
    bm.add_platform('.*posix.*', [
        ('add', '/posix/add/path'),
        ('sub', '/posix/sub/path'),
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
