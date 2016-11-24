from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task


def main():
    tq = TaskQueue()

    bm = BinaryManager()
    bm.add_platform('.*ix.*', [
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
