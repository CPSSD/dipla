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

    # Paths are a dict of task binaries and then platforms 
    binary_paths = {
        'add': {
            'posix': '/posix/add/path',
            'win32': '/win32/sub/path.exe',
        },
        'sub': {
            'posix': '/posix/sub/path',
            'win32': '/win32/add/path.exe',
        },
    }

    s = Server(tq, binary_paths)
    print('Starting server')
    s.start()

if __name__ == '__main__':
    main()