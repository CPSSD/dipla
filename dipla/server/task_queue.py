""" Task Queue

This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue

class TaskQueue:

    def __init__(self):
        self.queue = queue.Queue()

    def add_task(self, data_instructions, task_instructions):
        self.queue.put(_QueueItem(data_instructions, task_instructions))

    # Return the task at the front of the queue, removing it from the
    # queue in the process
    def pop_task(self):
        return self.queue.get()

    # Return the task at the front of the queue without removing it
    # from the queue
    def peek_task(self):
        return self.queue.queue[0]
        
# Abstraction of the information necessary to represent a task
class _QueueItem:

    def __init__(self, data_instructions, task_instructions):
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
