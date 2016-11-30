"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue  # needed to inherit exception from
import sys

class TaskQueue:
    """
    The TaskQueue is, as the name suggests, a FIFO queue for storing Tasks that
    should be executed by the workers. It has a set of active tasks that can be
    used to pop task values for clients to operate on. The active tasks set can
    build up as more tasks become available, and can decrease in size if some
    tasks are marked as completely finished receiving input
    """

    def __init__(self):
        # The queue head and tail represent the uids of the start and
        # end nodes respectively of a LinkedList
        self.active_tasks = set()
        self.nodes = {}

    def push_task(self, item):
        """
        Adds a task to the queue, connecting it with the tasks that it
        depends on. A task is connected to something it depends on 
        using a DataSource, which tracks the task that the data is
        coming from and the iterator that is used to stream the data

        Params:
         - item: The Task to be connected into the queue

        Returns
         - None
        """
        self.nodes[item.task_uid] = TaskQueueNode(item)

        # This task does not do anything, raise an error 
        if len(item.data_instructions) == 0:
           raise NoTaskDependencyError(
               "Attempted to add a task that did not have any data source") 

        # Inform all tasks that this one depends on about the dependancy
        active = True
        for instruction in item.data_instructions:
            # If instruction is from an iterable then it wont be a task
            if instruction.source_task_uid == None:
                continue

            # Inform other task that this task depends on it
            self.nodes[instruction.source_task_uid].add_dependee(item.task_uid)
            # If other task is not open, do not activate this task
            if not self.is_task_open(instruction.source_task_uid):
                active = False

        if active:
            self.active_tasks.add(item.task_uid)

    def has_next_input(self):
        """
        Returns true if there are task input values that can be popped
        from the queue, or false if there are either no tasks or no
        available values for any tasks
        """
        if len(self.active_tasks) == 0:
            return False

        for task_uid in self.active_tasks:
            if self.nodes[task_uid].has_next_input():
                return True

        return False

    # TODO(StefanKennedy) Add fallback incase popped values are lost
    # and we need to redistribute them
    def pop_task_input(self):
        """
        Returns some values that can be used to run a task as a
        TaskInput object. These values will be taken from a task
        with its id present in the active_tasks set

        Raises:
         - TaskQueueEmpty exception is there's no available tasks or
        no data available to return for any of the available tasks

        Returns:
         - The TaskInput object representing some of the data from an
        active task
        """
        if not self.has_next_input():
            raise TaskQueueEmpty("Queue was empty and could not pop input")

        for task_uid in self.active_tasks:
            if self.nodes[task_uid].has_next_input():
                return self.nodes[task_uid].next_input()

    def add_result(self, task_id, result):
        self.nodes[task_id].task_item.add_result(result)
        if self.is_task_open(task_id):
            self.activate_new_tasks(self.nodes[task_id].dependees)

    # TODO(StefanKennedy) Add functionality to close a task (take out of
    # active task set) This would happen if reading an input hit EOF

    def activate_new_tasks(self, ids):
        """
        Checks the tasks using the set of ids to try to move some more
        tasks into the active_tasks set. If a task has a dependency
        that is not open, it will not make the task open
        """
        for id in ids:
            # Check to see if the task still needs to wait on anything
            can_activate = True
            for dependency in self.nodes[id].dependencies:
                if not self.is_task_open(dependency.source_task_uid):
                    can_activate = False
                    break

            if can_activate:
                self.active_tasks.add(id)

    def is_task_open(self, task_uid):
        return self.nodes[task_uid].task_item.open

class TaskQueueEmpty(queue.Empty):
    """
    An exception to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


class TaskQueueNode:

    def __init__(self, task_item):
        """
        task_item is the value stored in this node

        This class acts as a node in a linked list using it's
        dependencies as the previous nodes and it's dependees as the
        next nodes
        """
        self.task_item = task_item
        self.dependencies = task_item.data_instructions
        self.dependees = []

    def add_dependee(self, dependee_uid):
        self.dependees.append(dependee_uid)

    def next_input(self):
        # TODO(StefanKennedy) Add functionality so that this can handle
        # multiple input dependencies
        if not self.dependencies[0].data_iterator.has_available_data():
            raise StopIteration("Attempted to read input from an empty source")

        return TaskInput(
            self.task_item.task_uid,
            self.task_item.task_instructions,
            self.dependencies[0].data_iterator.read())

    def has_next_input(self):
        for dependency in self.dependencies:
            if not dependency.data_iterator.has_available_data():
                return False
        return True

class DataSource:

    def read_all_values(stream):
        # Copy the values to a new list and return it
        return list(stream)

    def any_data_available(stream):
        return len(stream) > 0

    @staticmethod
    def create_source_from_task(
            task,
            read_function=read_all_values,
            availability_check=any_data_available):
        return DataSource(
            task.task_uid,
            DataIterator(task.task_output, read_function, availability_check))

    @staticmethod
    def create_source_from_iterable(
            iterable,
            read_function=read_all_values,
            availability_check=any_data_available):
        return DataSource(
            None, DataIterator(iterable, read_function, availability_check))

    def __init__(self, source_task_uid, data_iterator):
        """
        This is a class composed of a DataIterator, which also contains
        information about what task the data is sourced from (if sourced
        from a task)

        source_task_uid is the unique identifier of the task that this
        data is sourced from. (For that task, the data is it's output)

        data_iterator is the DataIterator object that contains the
        stream used to read the data
        """
        self.source_task_uid = source_task_uid
        self.data_iterator = data_iterator

class DataIterator:

    def __init__(self, stream, read_function, availability_check):
        """
        This is singly responsible for acting as the bridge between a 
        reader and a outputter of a stream of data. It should be
        composed by the reader, where the outputter has access to output
        on the stream

        stream is the collection of data that can be mutated by the
        reader as it consumes the values in it
        
        read_function is the defined way of reading values and returning
        the to the reader

        availability_check is the defined way of returning True or False
        depending on whether a call to read_function is possible on the
        stream
        """
        self.stream = stream
        self.read_function = read_function
        self.availability_check = availability_check
        # TODO(StefanKennedy) Test that this can add new values in a
        # streaming format.

    def has_available_data(self):
        return self.availability_check(self.stream) 

    def read(self):
        if not self.has_available_data():
            raise StopIteration("Attempted to read unavailable data")
        return self.read_function(self.stream)

class TaskInput:

    def __init__(self, task_uid, task_instructions, values):
        """
        This is what is given out by the task queue when some values
        are requested from a pop/peek etc. The values attribute
        is real data (as opposed to a promise) that will be sent to
        clients who then run it

        task_uid is the unique identifier of this instance of the task

        task_instructions are used to inform clients which runnable to
        execute

        values are the actual data values (not a promise) that are sent
        to clients to execute the task and return the results
        """
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
         - open_check:  A function that returns true if it can determine
        that this task is open. This function should take one argument 
        which is the result that is received from the client The default
        lambda function used here causes the completion check to return
        true when any result is received back from the server
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

class NoTaskDependencyError(Exception):
    """
    An exception to be thrown if the a task is added that depends on
    nothing. If this was possible, the task would never do anything
    """
    pass

