"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue # needed to inherit exception from

class TaskQueue:
    """
    The TaskQueue is, as the name suggests, a FIFO queue for storing Tasks that
    should be executed by the workers. It also has a pool of waiting tasks that
    have not received enough data inputs to be executed, and a pool of data
    that is expecting to go into a task but no task is yet waiting for it.
    """

    def __init__(self):
        # The queue head and tail represent the start and end nodes
        # respectively of a LinkedList
        self.queue_head = None
        self.queue_tail = None

        # A list of (data_type, value) tuples
        self.ready_data = []
        # A list of Tasks that do not have all the data they need yet
        self.waiting_tasks = []

    def push_task(self, item):
        """
        Adds a task to the queue, or to the pool of waiting tasks if it
        is still waiting on data.

        Params:
         - item: The Task to be executed by a worker

        Returns
         - None
        """

        if not item.ready():
            # If the item is still waiting on data, then we want to add
            # it to the store of waiting tasks
            self.waiting_tasks.append(item)
            return

        # If the LinkedList is empty
        if self.queue_head is None:
            # Set this item as the head and tail of the list
            self.queue_head = TaskQueueNode(item, container_queue=self)
            self.queue_tail = self.queue_head
        else:
            # Add an item to the end of the list
            new_node = TaskQueueNode(
                item, container_queue=self, previous_node=self.queue_tail)
            self.queue_tail.next_node = new_node
            self.queue_tail = new_node

    def update_waiting_tasks(self):
        """Taking the newly received data, see if any tasks are now ready
        to go."""
        # Iterate backwards so we can delete things without messing up
        # indexes
        for i in range(len(self.ready_data)-1, -1, -1):
            data_type, value = self.ready_data[i]
            found = False
            # Find a task that needs this data, and give it to it
            for j in range(len(self.waiting_tasks)):
                if self.waiting_tasks[j].requires_type(data_type):
                    found = True
                    self.waiting_tasks[j].give_data(data_type, value)
                    break
            if found:
                del self.ready_data[i]

        # Check for tasks that are ready to go
        for i in range(len(self.waiting_tasks)-1, -1, -1):
             if self.waiting_tasks[i].ready():
                 # Add this task to the live queue
                 self.push_task(self.waiting_tasks[i])
                 # Delete this task from the waiting list
                 del self.waiting_tasks[i]
                 
    def add_new_data(self, data_type, value):
        """Add some new data to the pool and see if it makes any tasks
        ready to go."""
        self.ready_data.append((data_type, value))
        self.update_waiting_tasks()

    def pop_task(self):
        """
        Removes a Task from the queue and returns it

        Raises
         - TaskQueueEmpty exception if there are no tasks

        Returns:
         - A Task object from the top of the queue
        """

        if self.queue_head is None:
            raise TaskQueueEmpty("Could not pop task from empty TaskQueue")

        next_head = self.queue_head.next_node
        popped = self.queue_head.pop()
        self.queue_head = next_head
        return popped

    def peek_task(self):
        """
        Returns the task at the front of the queue without removing it from
        the queue

        Raises:
         - TaskQueueEmpty exception is there's no tasks in the queue

        Returns:
         - The Task object at the top of the queue
        """
        if self.queue_head is None:
            raise TaskQueueEmpty("Queue was empty and could not peek item")

        return self.queue_head.task_item


class TaskQueueEmpty(queue.Empty):
    """
    An exception to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


# LinkedList Node containing the Task object
class TaskQueueNode:

    def __init__(self, task_item, container_queue,
                 previous_node=None, next_node=None):
        """
        task_item is the value stored in this node

        container_queue is the queue that this node was instantiated from.
        This needs to be tracked in order to empty the queue if this is
        the last existing node and it is deleted

        previous_node/next_node point to the corresponding node in the
        LinkedList
        """
        self.container_queue = container_queue
        task_item.container_node = self

        self.task_item = task_item
        self.previous_node = previous_node
        self.next_node = next_node

    def pop(self):
        del self.task_item.container_node

        # If this is the only item in the LinkedList
        if self.previous_node is None and self.next_node is None:
            self.container_queue.queue_head = None
            self.container_queue.queue_tail = None
            return self.task_item

        # If there are other items in the LinkedList reassign the
        # previous/next pointers of the neighbour items
        if self.previous_node is not None:
            self.previous_node.next_node = self.next_node
        if self.next_node is not None:
            self.next_node.previous_node = self.previous_node

        return self.task_item


# Abstraction of the information necessary to represent a task
class Task:
    """
    This is a class that should encapsulate all the information a client needs
    to excecute a piece of work.
    """

    def __init__(self, data_instructions, task_instructions,
                 completion_check=lambda x: True):
        """
        Initalises the Task

        Params:
         - data_instructions: A list of DataInstructions
         - task_instructions: An object used to represent instructions
        on what task should be carried out on the data
         - completion_check:  A function that returns true if it can
        determine that this task is complete. This function should take
        one argument which is the result that is received from the client
        The default lambda function used here causes the completion check
        to return true when any result is received back from the server
        """
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
        self.completion_check = completion_check
        self.completed = False

    @staticmethod
    def create(task_instructions,
        expected_data,
        completion_check=lambda x:True):
        """Create a Task.

        Params:
         - task_instructions: See __init__
         - expected_data: A dict in the form of {name:type}, where both
        "name" and "type" are strings. "name" refers to the name of a
        DataInstruction that this Task will need as input, and "type"
        refers to the type of that DataInstruction.
         - completion_check: See __init__

        Example usage:
        Task.create('add', {'a': 'number', 'b': 'number })

        Returns:
        A Task.
        """
        data_instructions = [DataInstruction(k, expected_data[k])
            for k in expected_data.keys()]
        return Task(data_instructions,
            task_instructions,
            completion_check)

    def add_result(self, result):
        if self.completion_check(result):
            self._complete_task()

    def _complete_task(self):
        if hasattr(self, "container_node"):
            # Take this element out of the LinkedList
            self.container_node.pop()
        self.completed = True

    def ready(self):
        """Returns True if the task has all the data it needs to run"""
        return all([x.ready() for x in self.data_instructions])

    def requires_type(self, data_type):
        return [x for x in self.data_instructions if (
            not x.ready() and x.get_type() == data_type)]

    def give_data(self, data_type, value):
        for i in range(len(self.data_instructions)):
            if ((not self.data_instructions[i].ready()) and
                self.data_instructions[i].get_type() == data_type):
                self.data_instructions[i].set_value(value) 
                return


class DataInstruction:
    """
    This is a class to hold a data input to a client binary.
    It can contain either immediate data ready to be used, or a
    piece of future data being waited on before being ready to be used.
    """

    def __init__(self, name, data_type="immediate", value=None):
        """Initialises the data instruction.

        Params:
         - name: The key that will be used for this piece of data when
        it is being passed to the binary.
         - data_type: A string with the type of data. This will be used
        to figure out if newly available data is relevant to a particular
        Task.
         - value: The actual value of this data instruction, of any type.
        """
        self.name = name
        # private, with a get_(), as some data may be drawn from a stream,
        # database, or similar.
        self._data_type = data_type
        self._value = value

    def ready(self):
        """Returns True if this DataInstruction is ready to be sent, and
        False if it is still waiting to be fulfilled."""
        return self._value is not None

    def get_value(self):
        """Returns the underlying data of this container."""
        return self._value

    def set_value(self, value):
        self._value = value

    def get_type(self):
        return self._data_type
