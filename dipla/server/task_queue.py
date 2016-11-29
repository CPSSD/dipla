"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue  # needed to inherit exception from
import sys

class TaskQueue:
    """
    The TaskQueue is, as the name suggests, a FIFO queue for storing Tasks that
    should be executed by the workers. It also has a pool of waiting tasks that
    have not received enough data inputs to be executed, and a pool of data
    that is expecting to go into a task but no task is yet waiting for it.
    """

    def __init__(self):
        # The queue head and tail represent the uids of the start and
        # end nodes respectively of a LinkedList
        self.active_tasks = set()
        self.nodes = {}

    def push_task(self, item):
        """
        Adds a task to the queue, connecting it with the tasks that it
        depends on. Some tasks will be input tasks, in which case they
        depend on nothing. A task is connected to something it depends
        on using a DataSource, which tracks the task that the data is
        coming from and the iterator that is used to stream the data

        Params:
         - item: The Task to be connected into the queue

        Returns
         - None
        """
        self.nodes[item.task_uid] = TaskQueueNode(item)

        # This task does not do anything, it has no inputs so dont make
        # it active (It must be an input task)
        if len(item.data_instructions) == 0:
            return

        # Inform all tasks that this one depends on about the dependancy
        active = True
        for instruction in item.data_instructions:
            # If instruction is from an iterable then it wont be a task
            if instruction.source_task_uid == None:
                continue

            # Inform other task that this task depends on it
            self.nodes[instruction.source_task_uid].add_dependee(item.task_uid)
            # If other task is not open, do not activate this task
            if not self.get_task_open(instruction.source_task_uid):
                active = False

        if active:
            self.active_tasks.add(item.task_uid)

    # TODO(StefanKennedy) Add fallback incase a client popped values are
    # lost and we need to redistribute them
    def pop_task_input(self):
        """
        Returns the task at the front of the queue without removing it from
        the queue

        Raises:
         - TaskQueueEmpty exception is there's no tasks in the queue

        Returns:
         - The Task object at the top of the queue
        """
        if len(self.active_tasks) == 0:
            raise TaskQueueEmpty("Queue was empty and could not pop input")

        for task_uid in self.active_tasks:
            if self.nodes[task_uid].has_next_input():
                return self.nodes[task_uid].next_input()

    def add_result(self, task_id, result):
        self.nodes[task_id].task_item.add_result(result)
        if self.get_task_open(task_id):
            self.activate_new_tasks(self.nodes[task_id].dependees)

    # TODO(StefanKennedy) Add functionality to close a task (take out of
    # active task set) This would happen if reading an input hit EOF

    # TODO(StefanKennedy) Test this
    def activate_new_tasks(self, ids):
        for id in ids:
            # Check to see if the task still needs to wait on anything
            can_activate = True
            for dependency in self.nodes[id].dependencies:
                if not self.get_task_open(dependency.task_uid):
                    can_activate = False
                    break

            if can_activate:
                self.active_tasks.add(id)

    def get_task_open(self, task_uid):
        return self.nodes[task_uid].task_item.open

class TaskQueueEmpty(queue.Empty):
    """
    An exception to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


# LinkedList Node containing the Task object
class TaskQueueNode:

    def __init__(self, task_item):
        """
        task_item is the value stored in this node

        container_queue is the queue that this node was instantiated from.
        This needs to be tracked in order to empty the queue if this is
        the last existing node and it is deleted

        previous_node/next_node point to the corresponding node in the
        LinkedList
        """
        self.task_item = task_item
        self.dependencies = task_item.data_instructions
        self.dependees = []

    def add_dependee(self, dependee_uid):
        self.dependees.append(dependee_uid)

    def next_input(self):
        # TODO(StefanKennedy) Add functionality so that this can handle
        # multiple input dependencies
        return TaskInput(
            self.task_item.task_uid,
            self.task_item.task_instructions,
            self.dependencies[0].data_iterator.read())

    def has_next_input(self):
        # TODO(StefanKennedy) Add functionality so that this can check
        # that it can get input from all dependencies
        return self.dependencies[0].data_iterator.has_available_data()

# A class composed of a DataIterator, which also contains information
# about what task the data is sourced from (if sourced from a task)
class DataSource:

    def read_all_values(stream): 
        return list(stream)

    @staticmethod
    def create_source_from_task(task, read_function=read_all_values):
        print("Creating data source from task with id: " + task.task_uid)
        return DataSource(
            task.task_uid, DataIterator(task.task_output, read_function))

    @staticmethod
    def create_source_from_iterable(iterable, read_function=read_all_values):
        return DataSource(None, DataIterator(iterable, read_function))

    def __init__(self, source_task_uid, data_iterator):
        self.source_task_uid = source_task_uid
        self.data_iterator = data_iterator

class DataIterator:

    def __init__(self, stream, read_function):
        self.stream = stream
        self.buffer = [x for x in stream]
        self.read_function = read_function
        # TODO(StefanKennedy) Set this up to add new values in a
        # streaming format. This currently just initalised itself to
        # whatever values are present in the stream

    def has_available_data(self):
        # TODO(StefanKennedy) Make this correspond to the read_function
        # supplied
        return len(self.buffer) > 0 

    def read(self):
        # TODO(StefanKennedy) Raise error if we run out of data
        return self.read_function(self.stream)

class TaskInput:

    def __init__(self, task_uid, task_instructions, values):
        self.task_uid = task_uid
        self.task_instructions = task_instructions
        self.values = values

# Abstraction of the information necessary to represent a task
class Task:
    """
    This is a class that should encapsulate all the information a client needs
    to excecute a piece of work.
    """

    def __init__(self, uid, task_instructions, open_check=lambda x: True):
        """
        Initalises the Task

        Params:
         - data_source: An iteratable object that can be used to read
        the input for this task
         - task_instructions: An object used to represent instructions
        on what task should be carried out on the data
         - completion_check:  A function that returns true if it can
        determine that this task is complete. This function should take
        one argument which is the result that is received from the client
        The default lambda function used here causes the completion check
        to return true when any result is received back from the server
        """
        self.task_uid = uid
        self.task_instructions = task_instructions
        self.data_instructions = []

        self.open_check = open_check
        self.open = False

        self.task_output = []

    def add_result(self, result):
        self.task_output.append(result)
        if self.open_check(result):
            self._open_task()

    def add_data_source(self, source):
        self.data_instructions.append(source)

    def _open_task(self):
        self.open = True
