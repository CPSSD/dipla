from dipla.shared.message_generator import generate_message
from dipla.server.task_queue import MachineType


class TaskInputDistributor:

    def __init__(self, worker_group, task_queue, verification_input_storer):
        self.__worker_group = worker_group
        self.__task_queue = task_queue
        self.__verification_input_storer = verification_input_storer

    def distribute_task(self):
        task_input = self.__get_next_task_input()
        if task_input is not None:
            self.__process_task_input(task_input)

    def __get_next_task_input(self):
        if not self.__worker_group.has_available_worker():
            if self.__task_queue.has_next_input(MachineType.server):
                return self.__task_queue.pop_task_input(MachineType.server)
        else:
            return self.__task_queue.pop_task_input()

    def __process_task_input(self, task_input):
        if self.__is_for_client(task_input):
            worker = self.__obtain_a_worker()
            self.__send_to_next_worker(worker, task_input)
            self.__potentially_store_input(worker, task_input)
        else:
            self.__copy_first_values_to_task_queue(task_input)

    def __is_for_client(self, task_input):
        return task_input.machine_type == MachineType.client

    def __obtain_a_worker(self):
        return self.__worker_group.lease_worker()

    def __send_to_next_worker(self, worker, task_input):
        message_object = self.__generate_run_instructions(task_input)
        worker.connection.send(message_object)

    def __potentially_store_input(self, worker, task_input):
        self.__verification_input_storer.potentially_store(
            worker,
            task_input
        )

    def __generate_run_instructions(self, task_input):
        data = {
            'task_instructions': task_input.task_instructions,
            'task_uid': task_input.task_uid,
            'arguments': task_input.values
        }
        return generate_message('run_instructions', data)

    def __copy_first_values_to_task_queue(self, task_input):
        for result in task_input.values[0]:
            self.__task_queue.add_result(task_input.task_uid, result)


class VerificationInputStorer:

    def __init__(self, inputs, probability, random_number_function):
        self.__inputs = inputs
        self.__probability = probability
        self.__random_number_function = random_number_function

    def potentially_store(self, worker, task_input):
        if self.__random_probability_is_met():
            self.__store_verification_input(task_input, worker)

    def __random_probability_is_met(self):
        random_number = self.__random_number_function()
        return random_number < self.__probability

    def __store_verification_input(self, task_input, worker):
        key = self.__generate_key(worker, task_input)
        value = self.__generate_value(worker, task_input)
        self.__inputs[key] = value

    def __generate_key(self, worker, task_input):
        return '{}-{}'.format(worker.uid, task_input.task_uid)

    def __generate_value(self, worker, task_input):
        return {
            'task_instructions': task_input.task_instructions,
            'inputs': task_input.values,
            'original_worker_uid': worker.uid
        }
