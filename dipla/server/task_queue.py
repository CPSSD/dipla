""" Task Queue

This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue


class TaskQueue:

    def __init__(self):
        self.queue = queue.Queue()

    def push_task(self, item):
        self.queue.put(item)

    # Return the task at the front of the queue, removing it from the
    # queue in the process
    def pop_task(self):
        if self.queue.qsize() == 0:
            raise TaskQueueEmpty("Could not pop task from empty TaskQueue")
        return self.queue.get()

    # Return the task at the front of the queue without removing it
    # from the queue
    def peek_task(self):
        if self.queue.qsize() == 0:
            raise TaskQueueEmpty("Queue was empty and could not peek item")
        return self.queue.queue[0]


class TaskQueueEmpty(queue.Empty):
    pass


# Abstraction of the information necessary to represent a task
class Task:

    def __init__(self, data_instructions, task_instructions):
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
