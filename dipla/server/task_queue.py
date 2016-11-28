"""
This module is a queue implementation for organising distributable tasks
using information such as the task identifier and input data
"""

import queue  # needed to inherit exception from
import sys

class TaskQueue:
    """
    The TaskQueue is, as the name suggests, a FIFO queue for storing Tasks that
    should be executed by the workers. It also has a pool of waiting tasks that
    have not received enough data inputs to be executed, and a pool of data
    that is expecting to go into a task but no task is yet waiting for it.
    """

    def __init__(self):
        # The queue head and tail represent the uids of the start and
        # end nodes respectively of a LinkedList
        self.queue_head = None
        self.queue_tail = None
        self.nodes = {}

    def push_task(self, item, dependencies=None):
        """
        Adds a task to the queue, or to the pool of waiting tasks if it
        is still waiting on data.

        Params:
         - item: The Task to be executed by a worker

        Returns
         - None
        """

        for dependency in dependencies:
            self.nodes[dependency].dependees.append(item.task_uid)

        # If the LinkedList is empty
        if self.queue_head is None:
            # Set this item as the head and tail of the list
            self.nodes[item.task_uid] = TaskQueueNode(item)
            self.queue_head = item.task_uid
            self.queue_tail = item.task_uid
        else:
            # Add an item to the end of the list
            self.nodes[item.task_uid] = TaskQueueNode(
                item, previous_node=self.queue_tail)
            self.nodes[self.queue_tail].next_node = item.task_uid
            self.queue_tail = item.task_uid

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

        next_head = self.nodes[self.queue_head].next_node
        popped = self._consume_node(self.queue_head)
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

        return self.nodes[self.queue_head].task_item

    def add_result(self, task_id, result):
        try:
            print("Adding result")
            self.nodes[task_id].task_item.add_result(result)
            print("Result added")
            if self.nodes[task_id].task_item.completed:
                self._consume_node(task_id)
                print("Completed!")
        except Exception as e:
            print("Exception: " + str(e))
            print("task_id " + task_id + " result " + str(result))

    def get_task_completed(self, task_uid):
        return self.nodes[task_uid].task_item.completed
    
    def _consume_node(self, task_id):
        node = self.nodes[task_id]

        # If this is the only item in the LinkedList
        if node.previous_node is None and node.next_node is None:
            self.queue_head = None
            self.queue_tail = None
            return node.task_item

        # If there are other items in the LinkedList reassign the
        # previous/next pointers of the neighbour items
        if node.previous_node is not None:
            self.nodes[node.previous_node].next_node = node.next_node
        if node.next_node is not None:
            self.nodes[node.next_node].previous_node = node.previous_node

        return node.task_item

class TaskQueueEmpty(queue.Empty):
    """
    An exception to be thrown if the TaskQueue is unexpectedly empty
    """
    pass


# LinkedList Node containing the Task object
class TaskQueueNode:

    def __init__(self, task_item, previous_node=None, next_node=None):
        """
        task_item is the value stored in this node

        container_queue is the queue that this node was instantiated from.
        This needs to be tracked in order to empty the queue if this is
        the last existing node and it is deleted

        previous_node/next_node point to the corresponding node in the
        LinkedList
        """
        self.task_item = task_item
        self.previous_node = previous_node
        self.next_node = next_node 
        self.dependees = []

    def add_dependee(self, dependee_uid):
        self.dependees.append(dependee_uid)


# Abstraction of the information necessary to represent a task
class Task:
    """
    This is a class that should encapsulate all the information a client needs
    to excecute a piece of work.
    """

    def __init__(self, uid, data_source, task_instructions,
                 completion_check=lambda x: True):
        """
        Initalises the Task

        Params:
         - data_source: An iteratable object that can be used to read
        the input for this task
         - task_instructions: An object used to represent instructions
        on what task should be carried out on the data
         - completion_check:  A function that returns true if it can
        determine that this task is complete. This function should take
        one argument which is the result that is received from the client
        The default lambda function used here causes the completion check
        to return true when any result is received back from the server
        """
        self.task_uid = uid
        self.data_source = data_source
        self.task_instructions = task_instructions
        self.completion_check = completion_check
        self.completed = False

    def add_result(self, result):
        print("Added result to task" + str(result))
        if self.completion_check(result):
            self._complete_task()

    def _complete_task(self):
        self.completed = True
