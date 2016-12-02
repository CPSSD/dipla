from dipla.server.server import Server, BinaryManager
from dipla.server.task_queue import TaskQueue, Task, DataSource
from dipla.shared import uid_generator

def generate_uid(existing):
    return uid_generator.generate_uid(
        length = 8, existing_uids=existing)

def main():
    tq = TaskQueue()
    
    root_source = [1, 2, 3, 4, 5]
    def consuming_read_function(stream):
        values = list(stream)
        stream.clear()
        return values

    # Create a first task that depends on root_source, a iterable
    # collection
    first_task_uid = generate_uid(existing=[]) 
    first_task = Task(first_task_uid, 'fibonacci')
    
    iterable_source_uid = generate_uid(existing=[])
    first_task.add_data_source(DataSource.create_source_from_iterable(
        root_source, iterable_source_uid, consuming_read_function))

    # Create a second task that depends on the first task's output
    second_task_uid = generate_uid(existing=[first_task_uid])
    second_task = Task(second_task_uid, 'fibonacci')

    first_task_source_uid = generate_uid(existing=[iterable_source_uid])
    second_task.add_data_source(DataSource.create_source_from_task(
        first_task, first_task_source_uid, consuming_read_function))

    tq.push_task(first_task)
    tq.push_task(second_task)

    bm = BinaryManager()
    bm.add_platform('.*x.*', [
        ('fibonacci', 'fibonacci')
    ])

    s = Server(tq, bm)
    print('Starting server')
    s.start()

if __name__ == '__main__':
    main()
