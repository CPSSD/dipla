from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task

def distributable_squarer(value):
    return value**2

def main():
    tq = TaskQueue()

    source = [1, 2, 3, 4, 5]
    tq.push_task(Task(source, 'fibonacci'))

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
