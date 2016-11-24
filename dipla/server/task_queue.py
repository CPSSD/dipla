"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue  # needed to inherit exception from


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

    def add_result(self, result):
        if self.completion_check(result):
            self._complete_task()

    def _complete_task(self):
        if hasattr(self, "container_node"):
            # Take this element out of the LinkedList
            self.container_node.pop()
        self.completed = True
