"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue


class TaskQueue:
    """
    The TaskQueue is, as the name suggests, a FIFO queue for storing Tasks that
    should be executed by the workers.
    """

    def __init__(self):
        self.queue = queue.Queue()

    def push_task(self, item):
        """
        Adds a task to the queue

        Params:
         - item: The Task to be executed by a worker

        Returns
         - None
        """
        self.queue.put(item)

    def pop_task(self):
        """
        Removes a Task from the queue and returns it

        Raises
         - TaskQueueEmpty exception if there are no tasks

        Returns:
         - A Task object from the top of the queue
        """
        if self.queue.qsize() == 0:
            raise TaskQueueEmpty("Could not pop task from empty TaskQueue")
        return self.queue.get()

    def peek_task(self):
        """
        Returns the task at the front of the queue without removing it from
        the queue

        Raises:
         - TaskQueueEmpty exception is there's no tasks in the queue

        Returns:
         - The Task object at the top of the queue
        """
        if self.queue.qsize() == 0:
            raise TaskQueueEmpty("Queue was empty and could not peek item")
        return self.queue.queue[0]


class TaskQueueEmpty(queue.Empty):
    """
    An expection to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


class Task:
    """
    This is a class that should encapsulate all the information a client needs
    to excecute a piece of work.
    """

    def __init__(self, data_instructions, task_instructions):
        """
        Initalises the Task

        Params:
         - data_instructions: The data to be passed to the binary
         - task_instructions: The binary that the worker should use for
        this task
        """
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
