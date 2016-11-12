from dipla.server.server import Server
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

    # Paths are a dict platforms and then task binaries
    binary_paths = {
        'posix': {
            'add': '/posix/add/path',
            'sub': '/posix/sub/path',
        },
        'win32': {
            'add': '/win32/add/path.exe',
            'sub': '/win32/sub/path.exe',
        },
    }

    s = Server(tq, binary_paths)
    print('Starting server')
    s.start()

if __name__ == '__main__':
    main()