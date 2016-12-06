"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue  # needed to inherit exception from
import sys
from enum import Enum


class TaskQueue:
    """
    The TaskQueue is, as the name suggests, an ordered LinkedList for storing
    Tasks that should be executed by the workers. It has a set of active tasks
    that can be used to pop task values for clients to operate on. The active
    tasks set can build up as more tasks become available, and can decrease in
    size if some tasks are marked as completely finished receiving input
    """

    def __init__(self):
        # _active_tasks is the set of all tasks ids for the tasks that
        # can currently have their inputs distributed to workers. Tasks
        # will be in this collection because everything they depend on
        # has had enough results for this task to be a feasible option
        # for distribution. If tasks are completed they will be removed
        # from this set. Since we may be streaming data, at a point in
        # time it is possible that all the data from the input stream
        # has been consumed and we need to wait on more before this task
        # can continue, but the task is still active in spite of this
        self._active_tasks = set()
        # _nodes are the TaskQueueNodes that make up the linked list
        # structure. The keys of the dictionary are the task ids and
        # the values are the TaskQueueNode objects
        self._nodes = {}

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
        if item.uid is None:
            raise AttributeError("Added task to TaskQueue with no id")
        self._nodes[item.uid] = TaskQueueNode(item)

        # Add this task as a dependant of all its prerequisite tasks
        active = True
        for instruction in item.data_instructions:
            # If instruction is from an iterable then it wont be a task
            if instruction.source_task_uid is None:
                continue

            # Inform other task that this task depends on it
            self._nodes[instruction.source_task_uid].add_dependee(item.uid)
            # If other task is not open, do not activate this task
            if not self.is_task_open(instruction.source_task_uid):
                active = False

        if active:
            self._active_tasks.add(item.uid)

    def has_next_input(self):
        """
        Returns true if there are task input values that can be popped
        from the queue, or false if there are either no tasks or no
        available values for any tasks
        """
        for task_uid in self._active_tasks:
            if self._nodes[task_uid].has_next_input():
                return True

        return False

    # TODO(StefanKennedy) Add fallback in case popped values are lost
    # and we need to redistribute them
    def pop_task_input(self):
        """
        Returns a TaskInput object that can be used to run a task as a
        These values will be taken from a task with its id present in
        the active_tasks set

        Raises:
         - TaskQueueEmpty exception is there's no available tasks or
        no data available to return for any of the available tasks

        Returns:
         - The TaskInput object representing some of the data from an
        active task
        """
        if not self.has_next_input():
            raise TaskQueueEmpty("Queue was empty and could not pop input")

        for task_uid in self._active_tasks:
            if self._nodes[task_uid].has_next_input():
                return self._nodes[task_uid].next_input()

    def add_result(self, task_id, result):
        if task_id not in self._nodes:
            raise KeyError(
                "Attempted to add result for a task not present in the queue")

        self._nodes[task_id].task_item.add_result(result)
        if self.is_task_open(task_id):
            self.activate_new_tasks(self._nodes[task_id].dependees)

    # TODO(StefanKennedy) Add functionality to close a task (take out of
    # active task set) This would happen if reading an input hit EOF

    def activate_new_tasks(self, ids):
        """
        Checks the tasks using the set of ids to try to move some more
        tasks into the active_tasks set. If a task has a dependency
        that is not open, it will not make the task open
        """
        for task_id in ids:
            if task_id not in self._nodes.keys():
                raise KeyError(
                    "Attempted to try activating a task that not in the queue")
            # Check to see if the task still needs to wait on anything
            can_activate = True
            for dependency in self._nodes[task_id].dependencies:
                if not self.is_task_open(dependency.source_task_uid):
                    can_activate = False
                    break

            if can_activate:
                self._active_tasks.add(task_id)

    def is_task_open(self, task_uid):
        if task_uid not in self._nodes:
            raise KeyError(
                "Attempted to check if task was open that is not in the queue")
        return self._nodes[task_uid].task_item.open

    def get_task_ids(self):
        return self._nodes.keys()


class TaskQueueEmpty(queue.Empty):
    """
    An exception to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


class TaskQueueNode:

    def __init__(self, task_item):
        """
        task_item is the value stored in this node

        This class acts as a node in a linked list using its
        dependencies as the previous nodes and it's dependees as the
        next nodes
        """
        self.task_item = task_item
        self.dependencies = task_item.data_instructions
        self.dependees = []

    def add_dependee(self, dependee_uid):
        self.dependees.append(dependee_uid)

    def next_input(self):
        if not self.dependencies[0].data_streamer.has_available_data():
            raise DataStreamerEmpty(
                "Attempted to read input from an empty source")

        arguments = []
        for dependency in self.dependencies:
            argument_id = dependency.source_uid
            arguments.append(dependency.data_streamer.read())
        return TaskInput(
            self.task_item.uid,
            self.task_item.instructions,
            arguments)

    def has_next_input(self):
        if len(self.dependencies) == 0:
            return False

        for dependency in self.dependencies:
            if not dependency.data_streamer.has_available_data():
                return False
        return True


class DataStreamerEmpty(Exception):
    """
    An exception raised when an attempt is made to read a data streamer,
    but there are currently no available values to read in the streamer
    """
    pass


class DataSource:

    def read_all_values(stream, location):
        # Copy the values to a new list and return it
        return list(stream)

    def any_data_available(stream, location):
        return len(stream) - location > 0

    def move_by_collection_size(collection, current_location):
        return current_location + len(collection)

    @staticmethod
    def create_source_from_task(
            task,
            source_uid,
            read_function=read_all_values,
            availability_check=any_data_available,
            location_changer=move_by_collection_size):
        return DataSource(source_uid, task.uid, DataStreamer(
            task.task_output,
            read_function,
            availability_check,
            location_changer))

    @staticmethod
    def create_source_from_iterable(
            iterable,
            source_uid,
            read_function=read_all_values,
            availability_check=any_data_available,
            location_changer=move_by_collection_size):
        return DataSource(source_uid, None, DataStreamer(
            iterable, read_function, availability_check, location_changer))

    def __init__(self, source_uid, source_task_uid, data_streamer):
        """
        This is a class composed of a DataStreamer, which also contains
        information about what task the data is sourced from (if sourced
        from a task)

        source_uid is the unique identifier of this object. It can be
        used to determine that the DataStreamer in this source was the
        origin of some data

        source_task_uid is the unique identifier of the task that this
        data is sourced from. (For that task, the data is it's output)

        data_streamer is the DataStreamer object that contains the
        stream used to read the data
        """
        self.source_uid = source_uid
        self.source_task_uid = source_task_uid
        self.data_streamer = data_streamer


class DataStreamer:

    def __init__(
            self,
            stream,
            read_function,
            availability_check,
            stream_location_changer=None):
        """
        This is singly responsible for acting as the bridge between a
        reader and a outputter of a stream of data. It should be
        composed by the reader, where the outputter has access to output
        on the stream

        stream is the collection of data that can be mutated by the
        reader as it consumes the values in it

        read_function is the function that is applied to the stream to
        read values in a particular way, e.g. one at a time, popping
        them from the collection, or read everything at once without
        consuming anything. This takes the stream and the stream
        location as an argument

        availability_check is the defined way of returning True or False
        depending on whether a call to read_function is possible on the
        stream. It takes the stream and the stream location as arguments

        stream_location_changer is a function that takes the data that
        was read, and the current stream_location integer, and the data
        that was read. The stream_location pointer will be set to the
        returned value

        stream_location is the current location through the stream that
        we have read to. This is the position the next read will start
        from
        """
        self.stream = stream
        self.read_function = read_function
        self.availability_check = availability_check
        self.stream_location_changer = stream_location_changer
        self.stream_location = 0

    def has_available_data(self):
        return self.availability_check(self.stream, self.stream_location)

    def read(self):
        if not self.has_available_data():
            raise DataStreamerEmpty("Attempted to read unavailable data")

        read = self.read_function(self.stream, self.stream_location)
        # Move the stream_location pointer to the new location. This is
        # for reading data without consuming it
        if self.stream_location_changer is not None:
            self.stream_location = self.stream_location_changer(
                read, self.stream_location)
        return read


class TaskInput:

    def __init__(self, task_uid, task_instructions, machine_type, values):
        """
        This is what is given out by the task queue when some values
        are requested from a pop/peek etc. The values attribute
        is real data (as opposed to a promise) that will be sent to
        clients who then run it

        task_uid is the unique identifier of this instance of the task

        task_instructions are used to inform clients which runnable to
        execute

        machine_type is an instance of the MachineType Enum, used to
        represent which type of machine this task should be run on

        values are the actual data values (not a promise) that are sent
        to clients to execute the task and return the results. It is a
        dictionary of the task_uid that this data is coming from (the
        source) to a list of the actual data values
        """
        self.task_uid = task_uid
        self.task_instructions = task_instructions
        self.machine_type = machine_type
        self.values = values


# Abstraction of the information necessary to represent a task
class Task:
    """
    This is a class that should encapsulate all the information a client needs
    to excecute a piece of work.

    A task is defined as open when it has produced enough results for the tasks
    that depend on it to be started. For example, this could be when the task
    produces any results. It could also be only whenever the task has produced
    all of the results that it will produce
    """

    def __init__(
            self,
            uid,
            task_instructions,
            machine_type,
            open_check=lambda x: True):
        """
        Initalises the Task

        Params:
         - uid: An identifier, different to the task/executable name
        that can be used to uniquely identify this task
         - task_instructions: An object used to represent instructions
        on what task should be carried out on the data
         - machine_type: A MachineType enum instance that determines
        what type of machine this task should be run on (e.g. Server,
        client)
         - open_check: A function that returns true if it can determine
        that this task is open. This function should take one argument
        which is the result that is received from the client The default
        lambda function used here causes the completion check to return
        true when any result is received back from the server. A task
        being open is defined in the docstring for the Task class
        """
        self.uid = uid
        self.instructions = task_instructions
        self.machine_type = machine_type
        self.data_instructions = []

        self.open_check = open_check
        self.open = False

        self.task_output = []

    def add_result(self, result):
        self.task_output.append(result)
        if self.open_check(result):
            self._open_task()

    def add_data_source(self, source):
        """
        The order in which data sources are added is important because
        it will be later used to manage the order of command line
        arguments for a binary
        """
        self.data_instructions.append(source)

    def _open_task(self):
        self.open = True


class MachineType(Enum):
    """
    An enum used to represent a type of machine
    """
    Server = 1
    Client = 2
