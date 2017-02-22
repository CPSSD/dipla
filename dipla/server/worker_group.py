"""
This module contains the WorkerGroup and other supporting classes. It is
intended for this file to contain the code to manage the workers.
"""
import heapq
import operator

from dipla.shared import uid_generator


class WorkerGroup:
    """
    A representation of a group of workers which is used to manage the
    order in which workers are chosen.

    This tracks which workers are available to start a new task, and which are
    currently running a task.
    """

    # TODO(StefanKennedy): Add functionality to choose another
    # worker when a busy worker disconnects

    def __init__(self, stats):
        """
        Initialise the worker group.

        Params:
         - stats: An instance of shared.statistics.StatisticsUpdater, needed
           here in order to update how many clients are connected right now.
        """

        self.__statistics_updater = stats
        # Ready Workers is a min heap, used to quickly find the most
        # preferrable worker during worker-leasing behaviour
        self.ready_workers = []
        self.busy_workers = {}

    def add_worker(self, worker):
        """
        Add a worker to the group in the 'ready' state.

        Params:
         - worker: The Worker object to be added.

        Raises:
         - ValueError when a worker with the same uid already exists in the
           group.
        """
        if worker.uid in self.worker_uids():
            raise ValueError("Unique ID " + worker.uid + " is already in use")
        heapq.heappush(self.ready_workers, worker)
        self.__statistics_updater.increment('num_total_workers')
        self.__statistics_updater.increment('num_idle_workers')

    def remove_worker(self, uid):
        """
        Removes a worker (identified by it's uid) from the group, irregardless
        of its state.

        Params:
         - uid: The unique ID of the worker to be removed.

        Raises:
         - KeyError if the uid provided does not match any of the workers in
           the group.
        """
        if uid in self.busy_workers:
            self.busy_workers.pop(uid)
            self.__statistics_updater.decrement('num_total_workers')
            return

        for i in range(len(self.ready_workers)):
            if self.ready_workers[i].uid == uid:
                self.ready_workers.pop(i)
                heapq.heapify(self.ready_workers)
                self.__statistics_updater.decrement('num_total_workers')
                self.__statistics_updater.decrement('num_idle_workers')
                return

        raise KeyError("No worker was found with the ID: " + uid)

    def lease_worker(self):
        """
        Choose a worker to mark leased so that this will not be used by another
        task at the same time. This must be returned later using return_worker
        so that the worker can be reused.

        Returns:
         - The highest quality available Worker
        """
        if len(self.ready_workers) == 0:
            raise IndexError("No workers available to lease")
        chosen = heapq.heappop(self.ready_workers)
        self.busy_workers[chosen.uid] = chosen
        self.__statistics_updater.decrement('num_idle_workers')
        return chosen

    def return_worker(self, uid):
        """
        Indicate that a leased Worker is no longer needed and can now be used
        by other tasks. The Worker object must not be used after it is
        returned.

        Params:
         - uid: The uid of the worker to be returned and marked as available

        Raises:
         - KeyError if the uid doesn't correspond to any leased workers
        """
        if uid not in self.busy_workers.keys():
            raise KeyError("No busy workers with the provided key")
        worker = self.busy_workers.pop(uid)
        heapq.heappush(self.ready_workers, worker)
        self.__statistics_updater.increment('num_idle_workers')

    def worker_uids(self):
        """
        Returns:
         - The uids of all workers, regardless of state
        """
        return [x.uid for x in self._all_workers()]

    def has_available_worker(self):
        """
        Returns:
         - True if there are workers available in the ready_worker set
        """
        return len(self.ready_workers) > 0

    def get_worker(self, uid):
        """
        Params:
         - uid: The unique ID of the worker to be returned.

        Raises:
         - KeyError if the uid does not match any workers in the group.
        """
        if uid in self.busy_workers:
            return self.busy_workers[uid]

        for i in range(len(self.ready_workers)):
            if self.ready_workers[i].uid == uid:
                return self.ready_workers[i]

        raise KeyError("No worker was found with the ID: " + uid)

    def _all_workers(self):
        """
        Returns:
         - A list of all the ready workers and busy workers
        """
        return self.ready_workers + list(self.busy_workers.values())

    def generate_uid(self):
        return uid_generator.generate_uid(length=8,
                                          existing_uids=self.worker_uids())


class WorkerIDsExhausted(Exception):
    pass


class Worker:
    """
    Abstraction of the information necessary to represent a worker in the
    WorkerGroup.
    """

    def __init__(self, uid, websocket, quality=None):
        """
        Initalises the worker. Workers are given a correctness score to
        indicate how correct the results have been that have been
        received from this worker. This score can be used to determine
        whether or not to continue using this worker

        Params:
         - uid: The worker's Unique Identifier string.
         - websocket: The worker's connected websocket.
         - quality: A numeric indicator of how preferrable this worker is for
           running a task. This could depend on the hosts ping, reliability,
           processing power, etc.
        """
        self.uid = uid
        self._quality = quality
        self.websocket = websocket

        self.correctness_score = 1.0
        self.current_task_instr = None
        self.last_inputs = None

    def set_quality(self, quality):
        """
        Sets the quality of the worker if not previously provided.

        Raises:
         - AttributeError: If quality has already been set
        """
        if self._quality is not None:
            raise AttributeError("Quality attribute already assigned")
        else:
            self._quality = quality

    def quality(self):
        """
        Provides a value for the quality of the worker. The closer to 0 the
        value is, the more preferable the worker. This value may differ from
        what was provided in the constructor.

        Returns:
         - An integer 'quality' value.
        """
        # Squaring the values here is a placeholder until a more
        # relevant quality formula is determined
        return self._quality * self._quality

    def __eq__(self, other):
        return self.quality() == other.quality()

    def __gt__(self, other):
        return self.quality() > other.quality()
