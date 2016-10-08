""" Task Queue

This module represents a queue of distributable tasks that can be executed using the information and functionality provided in this module
"""

import queue

class TaskQueue:

    def __init__(self):
        self.queue = queue.Queue()

    def add_task(self, data_instructions, task_instructions):
        self.queue.put(_QueueItem(data_instructions, task_instructions))
        
class _QueueItem:

    def __init__(self, data_instructions, task_instructions):
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
