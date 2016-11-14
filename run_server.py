from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task


def main():
    tq = TaskQueue()
    tasks = [
        Task.create('add', {'x': 'int', 'y': 'int'}),
        Task.create('add', {'x': 'int', 'y': 'int'}),
        Task.create('add', {'x': 'int', 'y': 'int'})
    ]
    for task in tasks:
        tq.push_task(task)
        print('Added task %s' % task.task_instructions)
    tq.add_new_data('int', 1)
    tq.add_new_data('int', 2)
    tq.add_new_data('int', 32)
    tq.add_new_data('int', 4)
    tq.add_new_data('int', 16)
    tq.add_new_data('int', 4)

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
