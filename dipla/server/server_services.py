from dipla.shared.logutils import LogUtils
from dipla.shared.services import ServiceError
from dipla.shared.error_codes import ErrorCodes


class ServerServices:

    def __init__(self, binary_manager, stats):
        """
        Raising an exception will transmit it back to the client. A
        ServiceError lets you include a specific error code to allow
        the client to better choose what to do with it.

        The services provided here expect a data object of type
        ServiceParams that carry the server that is calling the service
        as well as the worker that owns the websocket that called the
        service

        binary_manager is a BinaryManager instance containing the task
        binaries that can be requested by a client
        stats is an instance of statistics.shared.StatisticsUpdater,
        used here to track the number of responses from clients.
        """
        self.services = {
            'get_binaries': self._handle_get_binaries,
            'binaries_received': self._handle_binary_received,
            'client_result': self._handle_client_result,
            'runtime_error': self._handle_runtime_error,
            'verify_inputs_result': self._handle_verify_inputs
        }
        self.binary_manager = binary_manager
        self.__statistics_updater = stats

    def get_service(self, label):
        if label in self.services:
            return self.services[label]
        raise KeyError("Label '{}' does not have a handler".format(label))

    def _handle_get_binaries(self, message, params):
        # Check if the worker has provided the correct password
        if params.server.password is not None:
            if 'password' not in message:
                raise ServiceError('Password required by server',
                                   ErrorCodes.password_required)
            elif message['password'] != params.server.password:
                raise ServiceError('Incorrect password provided',
                                   ErrorCodes.invalid_password)
        # Set the workers quality
        params.worker.set_quality(message['quality'])
        # Find the correct binary for the worker
        platform = message['platform']
        try:
            encoded_bins = self.binary_manager.get_binaries(platform)
        except KeyError as e:
            raise ServiceError(e, ErrorCodes.invalid_binary_key)

        data = {
            'base64_binaries': dict(encoded_bins),
        }
        return data

    def _handle_binary_received(self, message, params):
        # Worker has downloaded binary and is ready to do tasks
        try:
            params.server.worker_group.add_worker(params.worker)
        except ValueError as e:
            raise ServiceError(e, ErrorCodes.user_id_already_taken)
        # If there was extra tasks that no others could do, try and
        # assign it to this worker, as it should be the only ready one
        # If there are other workers it is okay to distribute tasks to
        # them too
        params.server.distribute_tasks()
        return None

    def _send_verify_inputs(self, server, results, worker_id, task_id):
        if not server.worker_group.has_available_worker():
            return
        # This will not verify results if the original data was not
        # previously stored on a probabilistic basis
        formatted_verify_key = worker_id + "-" + task_id
        if formatted_verify_key not in server.verify_inputs:
            return

        verify_data = server.verify_inputs.pop(formatted_verify_key)
        # Add the results to verification data creating an object
        # with both the inputs and the results
        verify_data['results'] = results

        # Send the verify inputs request to a client
        leased_worker = server.worker_group.lease_worker()
        data = {}
        data['task_instructions'] = verify_data['task_instructions']
        data['task_uid'] = task_id
        data['arguments'] = verify_data['inputs']
        server.send(leased_worker.websocket, 'verify_inputs', data)

        # Add the verification input / results data back to the map
        # under the new worker id
        new_dict_key = leased_worker.uid + '-' + task_id
        server.verify_inputs[new_dict_key] = verify_data

    def _handle_client_result(self, message, params):
        task_id = message['task_uid']
        results = message['results']
        server = params.server
        worker = params.worker
        self.__statistics_updater.adjust("num_results_from_clients",
                                         len(results))
        
        t_instr = worker.current_task_instr
        if server.result_verifier.has_verifier(t_instr):
            # Iterate through inputs and outputs, verifying each

            # The last_inputs is a list containing lists, each of which
            # represents the next N inputs from a data source. So the 0th
            # element in `results` is computed from the 0th elements of each
            # of the lists in worker.last_inputs and so on.
            # The following line "rotates" this 2d list structure so that the
            # 0th element in `input_lists` is the list of inputs used to get
            # the 0th result in `results`
            input_lists = zip(*worker.last_inputs)
            for inp, result in zip(input_lists, results):
                if server.result_verifier.check_output(t_instr, inp, result):
                    server.task_queue.add_result(task_id, result)
                else:
                    # TODO(Cian): Add input back into the list of things to do.
                    # Currently the task will never be market as complete and
                    # the server won't exit if the verification fails as it's
                    # still expecting another result.
                    e = ("{} verifier declared output '{}' incorrect "
                         "for input '{}'")
                    LogUtils.warning(e.format(t_instr, result, inp))
        else:
            # If no verification, add everything to task_queue
            for result in results:
                server.task_queue.add_result(task_id, result)

        # We need to send verify_inputs before returning the worker so
        # that we dont send it to the original worker
        self._send_verify_inputs(server, results, worker.uid, task_id)
        server.worker_group.return_worker(worker.uid)
        server.distribute_tasks()
        return None

    def _handle_runtime_error(self, message, params):
        print('Client had an error (code %d): %s' % (message['code'],
                                                     message['details']))
        return None

    def _handle_verify_inputs(self, message, params):
        verify_inputs_key = params.worker.uid + '-' + message['task_uid']
        verify_data = params.server.verify_inputs[verify_inputs_key]

        original_worker = params.server.worker_group.get_worker(
            verify_data["original_worker_uid"])
        if verify_data['results'] != message['results']:
            original_worker.correctness_score -= 0.05
            if original_worker.correctness_score <\
                    params.server.min_worker_correctness:
                params.server.worker_group.remove_worker(
                    verify_data["original_worker_uid"])
                LogUtils.debug(
                    "Removing " + original_worker.uid + " for invalid results")
        else:
            original_worker.correctness_score += 0.05
            params.server.worker_group.return_worker(params.worker.uid)

        del params.server.verify_inputs[verify_inputs_key]


class ServiceParams:

    def __init__(self, server, worker):
        self.server = server
        self.worker = worker
