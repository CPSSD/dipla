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
        if item.is_reduce:
            group_size = item.reduce_group_size
            self._nodes[item.uid] = ReduceTaskQueueNode(item, group_size)
        else:
            self._nodes[item.uid] = TaskQueueNode(item)

        # Add this task as a dependant of all its prerequisite tasks
        active = True
        for instruction in item.data_instructions:
            # If instruction is from an iterable then it wont be a task
            # and wont have a task id
            if instruction.source_task_uid is None:
                continue

            # Inform other task that this task depends on it
            self._nodes[instruction.source_task_uid].add_dependee(item.uid)
            # If other task is not open, do not activate this task
            if not self.is_task_open(instruction.source_task_uid):
                active = False
        if active:
            self._active_tasks.add(item.uid)

    def push_task_input(self, task_id, inputs):
        """
        Adds more input for a task. This will raise a ValueError if
        inputs is not suitable for pushing as task input

        task_id is the id of the task that these inputs will be added
        for

        inputs is a multidimensional list. The first dimension indexes
        the i'th argument/parameter to the task. The second dimension
        represents the values that are passed as that parameter in the
        order they should be inputted
        """
        if task_id not in self._nodes:
            raise KeyError(
                "Attempted to add input to unknown task id", task_id)

        if len(inputs) != len(self._nodes[task_id].dependencies):
            raise ValueError(
                "Attempted to add input with mismatching number of arguments")

        for i in range(len(inputs)):
            self._nodes[task_id].dependencies[i].data_streamer.add_inputs(
                inputs[i])

    def has_next_input(self, machine_type=None):
        """
        Returns true if there are task input values that can be popped
        from the queue, or false if there are either no tasks or no
        available values for any tasks

        machine_type is an instance of the MachineType enum. If
        specified, this has_next method will only consider tasks of
        this type. If this parameter is None it will have
        MachineType.any_machine assigned to it
        """
        if machine_type is None:
            machine_type = MachineType.any_machine
        for task_uid in self._active_tasks:
            if not self._nodes[task_uid].is_machine_type(machine_type):
                continue

            if self._nodes[task_uid].has_next_input():
                return True

        return False

    # TODO(StefanKennedy) Add fallback in case popped values are lost
    # and we need to redistribute them
    def pop_task_input(self, machine_type=None):
        """
        Returns a TaskInput object that can be used to run a task as a
        These values will be taken from a task with its id present in
        the active_tasks set

        machine_type is a MachineType enum instance indicating what type
        of task input should be popped (Input for a task that will run
        on the specified machine.) If this parameter is None it will
        have MachineType.any_machine assigned to it

        Raises:
         - TaskQueueEmpty exception is there's no available tasks or
        no data available to return for any of the available tasks

        Returns:
         - The TaskInput object representing some of the data from an
        active task
        """
        if machine_type is None:
            machine_type = MachineType.any_machine

        if not self.has_next_input(machine_type):
            raise TaskQueueEmpty("Queue was empty and could not pop input")

        for task_uid in self._active_tasks:
            if not self._nodes[task_uid].is_machine_type(machine_type):
                continue

            if self._nodes[task_uid].has_next_input():
                # Read some data from this task, and if check if we've
                # completed it
                return self._nodes[task_uid].next_input()

    def add_result(self, task_id, result):
        if task_id not in self._nodes:
            raise KeyError(
                "Attempted to add result for a task not present in the queue")

        self._nodes[task_id].task_item.add_result(result)
        if self._nodes[task_id].task_item.is_reduce:
            # This task has been marked as a reduce task, so outputs should be
            # put back into the same task as an input.

            # self.push_task_input() expects a series of groups of inputs,
            # (one group of inputs is the things a task needs to run once)
            # so we must turn this single value into that format
            args = [[result]]
            self.push_task_input(task_id, args)

        if self.is_task_open(task_id):
            self.activate_new_tasks(self._nodes[task_id].dependees)
        # Check if the task is now completed
        if self.is_task_complete(task_id):
            self._active_tasks.remove(task_id)

    def get_task(self, task_uid):
        return self._nodes[task_uid].task_item

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
                if dependency.source_task_uid is None:
                    continue
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

    def get_task_by_id(self, task_uid):
        if task_uid not in self._nodes:
            raise KeyError(
                "Attempted to get a get a task that is not in the queue")
        return self._nodes[task_uid].task_item

    def is_task_complete(self, task_uid):
        if task_uid not in self._nodes:
            raise KeyError(
                "Tried to check if task was complete that is not in the queue")
        return self._nodes[task_uid].task_item.complete

    def is_inactive(self):
        return len(self._active_tasks) == 0

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
            arg = dependency.data_streamer.read()
            # Client expects a list of arguments
            if not isinstance(arg, list):
                arg = [arg]
            arguments.append(arg)

        # Not very pretty, but expect a result for every element in the args
        self.task_item.inc_expected_results_by(len(arguments[0]))
        return TaskInput(
            self.task_item.uid,
            self.task_item.instructions,
            self.task_item.machine_type,
            arguments,
            signals=list(self.task_item.signals))

    def has_next_input(self):
        if len(self.dependencies) == 0:
            return False

        for dependency in self.dependencies:
            if not dependency.data_streamer.has_available_data():
                return False
        return True

    def is_machine_type(self, machine_type):
        if machine_type == MachineType.any_machine:
            return True
        return machine_type == self.task_item.machine_type


class ReduceTaskQueueNode(TaskQueueNode):

    def __init__(self, task_item, reduce_group_size):
        super().__init__(task_item)
        self.reduce_group_size = reduce_group_size

    def next_input(self):
        if not self.dependencies[0].data_streamer.has_available_data():
            raise DataStreamerEmpty(
                "Attempted to read input from an empty source")
        arguments = []

        for _ in range(self.reduce_group_size):
            dependency = self.dependencies[0]
            if not dependency.data_streamer.has_available_data():
                break
            argument_id = dependency.source_uid
            arg = dependency.data_streamer.read()

            arguments.append(arg[0])

            # if we are not adding things one by one
            if len(arguments) >= self.reduce_group_size:
                break
        arguments = [[arguments]]

        # Not very pretty, but expect a result for every element in the args
        self.task_item.inc_expected_results_by(len(arguments[0]))
        return TaskInput(
            self.task_item.uid,
            self.task_item.instructions,
            self.task_item.machine_type,
            arguments,
            signals=list(self.task_item.signals))


class DataStreamerEmpty(Exception):
    """
    An exception raised when an attempt is made to read a data streamer,
    but there are currently no available values to read in the streamer
    """
    pass


class DataSource:

    def read_all_values(stream, location):
        # Copy the values to a new list and return it
        return list(stream)[location:]

    def read_one_value(stream, location):
        return list(stream)[location:location+1]

    def any_data_available(stream, location):
        return len(stream) - location > 0

    def move_by_collection_size(collection, current_location):
        return current_location + len(collection)

    def move_by_one(stream, current_location):
        return current_location + 1

    @staticmethod
    def create_source_from_task(
            task,
            source_uid,
            read_function=read_one_value,
            availability_check=any_data_available,
            location_changer=move_by_one):
        return DataSource(source_uid, task.uid, DataStreamer(
            task.task_output,
            read_function,
            availability_check,
            location_changer))

    @staticmethod
    def create_source_from_iterable(
            iterable,
            source_uid,
            read_function=read_one_value,
            availability_check=any_data_available,
            location_changer=move_by_one):
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

    def add_inputs(self, inputs):
        """
        inputs is a list of values that sould be outputted from this
        DataStreamer when it is read
        """
        self.stream.extend(inputs)


class TaskInput:

    def __init__(self,
                 task_uid,
                 task_instructions,
                 machine_type,
                 values,
                 signals={}):
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

        signals is a list of reserved signal keywords for this input
        """
        self.task_uid = task_uid
        self.task_instructions = task_instructions
        self.machine_type = machine_type
        self.values = values
        self.signals = signals


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
            open_check=lambda x: True,
            complete_check=lambda x: False,
            signals={},
            is_reduce=False,
            reduce_group_size=2):
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
         - complete_check: A function that returns true if it can
        determine that this task should be completed, and no longer
        be used for any distributed operation. This defaults to a
        function that always returns False so that the task does not
        close. This takes the remaining, unread stream as an argument
         - signals: A dict with keys as words that should be detected
        in the output of the task as signals and sent to the server for
        processing. The values are the functions that should be used to
        process that inputs from that signal
        """
        self.uid = uid
        self.instructions = task_instructions
        self.machine_type = machine_type
        self.is_reduce = is_reduce
        self.reduce_group_size = reduce_group_size
        self.data_instructions = []

        self.open_check = open_check
        self.open = False
        self.complete_check = complete_check
        self.complete = False
        self.num_expected_results = 0
        self.num_seen_results = 0

        self.signals = signals
        self.task_output = []

    def inputs_exhausted(self):
        for source in self.data_instructions:
            # If any dependencies do not have data available the
            if self.complete_check(source.data_streamer):
                return True
        return False

    def add_result(self, result):
        self.task_output.append(result)
        self.num_seen_results += 1
        # If our inputs have nothing left in them and we've recieved the
        # number of results we expect then this task is complete
        self.complete = (self.inputs_exhausted() and
                         self.num_seen_results == self.num_expected_results)
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

    def inc_expected_results_by(self, count):
        # Increase the number of results we should expect
        self.num_expected_results += count


class MachineType(Enum):
    """
    An enum used to represent a type of machine
    """
    server = 1
    client = 2
    any_machine = 3
