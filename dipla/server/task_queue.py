""" Task Queue

This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue


class TaskQueue:
    
    def __init__(self):
        self.queue_head = None

    def push_task(self, item):
        if self.queue_head == None:            
            self.queue_head = TaskQueueNode(item, previous_node = None,
                                            next_node = None)
            self.queue_tail = self.queue_head
        else:
            new_node = TaskQueueNode(item, previous_node = self.queue_tail,
                                     next_node = None)
            self.queue_tail.next_node = new_node 
            self.queue_tail = new_node

    # Return the task at the front of the queue, removing it from the
    # queue in the process
    def pop_task(self):
        if self.queue_head == None:
            raise TaskQueueEmpty("Could not pop task from empty TaskQueue")

        popped = self.queue_head.pop()
        self.queue_head = self.queue_head.next_node
        return popped

    # Return the task at the front of the queue without removing it
    # from the queue
    def peek_task(self):
        if self.queue_head == None:
            raise TaskQueueEmpty("Queue was empty and could not peek item")

        return self.queue_head.task_item


class TaskQueueEmpty(queue.Empty):
    pass


# LinkedList Node containing the Task object
class TaskQueueNode:

    def __init__(self, task_item, previous_node, next_node):
        task_item.container_node = self

        self.task_item = task_item
        self.previous_node = previous_node
        self.next_node = next_node

    def pop(self):
        del self.task_item.container_node
        if not self.previous_node == None:
            self.previous_node.next_node = self.next_node
        if not self.next_node == None:
            self.next_node.previous_node = self.previous_node
        return self.task_item


# Abstraction of the information necessary to represent a task
class Task:

    def complete_on_any_result(result):
        return True

    def __init__(self, data_instructions, task_instructions,
                 completion_check = complete_on_any_result):
        self.data_instructions = data_instructions
        self.task_instructions = task_instructions
        self.completion_check = completion_check

    def add_result(self, result):
        if self.completion_check(result):
            self.complete_task()

    def _complete_task(self):
        if not self.container_node == None:
            # Take this element out of the LinkedList
            self.container_node.pop()

