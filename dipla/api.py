import json
from multiprocessing import Process
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dipla.api_support import script_templates
from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.dashboard import DashboardServer
from dipla.server.result_verifier import ResultVerifier
from dipla.server.server import BinaryManager, Server, ServerServices
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator, statistics
from dipla.client.client_factory import ClientFactory
from dipla.client.config_handler import ConfigHandler


class Dipla:

    # BinaryManager, TaskQueue and ResultVerifier to be injected into server.
    task_queue = TaskQueue()
    result_verifier = ResultVerifier()
    _password = None
    _stats = {
        "num_total_workers": 0,
        "num_idle_workers": 0,
        "start_time": "",
        "num_results_from_clients": 0,
    }
    stat_updater = statistics.StatisticsUpdater(_stats)
    # This is a dictionary of function id to a function that creates a
    # task. The id is obtained using id(x) where x is an object that
    # should have a task creator associated with it. The function should
    # take two parameters, the task/iterable being sourced from and the
    # name of the task being performed on that source
    _task_creators = dict()
    # Dictionary of function id to function object. Check the comments
    # for Dipla_task_creators for details on how the id is determined.
    _task_functions = dict()
    # This is a dictionary of functon id to tuples, where the first
    # value is the input script wrapper, and the second is a dictionary
    # of a signal to a function that processes the input received from
    # this signal. This embedded dict should contain a key for each
    # signal registered under the function. Check the comments for
    # Dipla_task_creators for details on how the id is determined.
    _task_input_script_info = dict()
    _reduce_task_group_sizes = dict()

    # Stop reading the data source once we hit EOF
    # TODO(StefanKennedy) Set up data sources to run indefinitely.
    @staticmethod
    def complete_on_eof(streamer):
        if streamer.stream_location >= len(streamer.stream):
            return True
        return False

    # TODO(StefanKennedy) There's a bit of tracking the number of
    # expected values for tasks, it's possible that using
    # complete_when_unavailable can avoid the need to track expected
    # values. Investigate this, it could clean up the code
    @staticmethod
    def complete_when_unavailable(streamer):
        return not streamer.has_available_data()

    @staticmethod
    def stream_not_empty(stream, location):
        return len(stream) > 0

    def _create_clientside_task(task_instructions, is_reduce=False, reduce_group_size=2):
        task_uid = uid_generator.generate_uid(
            length=8,
            existing_uids=Dipla.task_queue.get_task_ids())
        return Task(
            task_uid,
            task_instructions,
            MachineType.client,
            complete_check=Dipla.complete_when_unavailable,
            is_reduce=is_reduce,
            reduce_group_size=reduce_group_size)

    def _generate_uid_in_list(uids_list):
        new_uid = uid_generator.generate_uid(length=8, existing_uids=uids_list)
        uids_list.append(new_uid)
        return new_uid

    def _add_sources_to_task(sources, task, create_data_source_function):
        """
        sources are the DataSource objects for the task. These can be
        iterables or other tasks

        task is the task that should have the sources added to it

        create_data_source_function is a function that returns a data
        source, it should take two parameters, a source from the sources
        list, and a DataSource.create_source_from_task or a
        DataSource.create_source_from_iterable function, used to create
        the data source
        """
        for source in sources:
            data_source_creator = DataSource.create_source_from_iterable
            if isinstance(source, Task):
                data_source_creator = DataSource.create_source_from_task
            task.add_data_source(
                create_data_source_function(source, data_source_creator))

    def _create_normal_task(sources, task_instructions, is_reduce=False, reduce_group_size=2):
        """
        sources are objects that can be used to create a data source,
        e.g. an iterable or another task
        """
        task = Dipla._create_clientside_task(task_instructions, is_reduce, reduce_group_size)

        source_uids = []

        def create_default_data_source(source, data_source_creator):
            return data_source_creator(source, source_uids)

        Dipla._add_sources_to_task(sources, task, create_default_data_source)
        return task

    def _process_decorated_function(function, verifier=None):
        function_id = id(function)
        Dipla._task_functions[function_id] = function
        if verifier:
            Dipla.result_verifier.add_verifier(
                function.__name__,
                verifier)

    @staticmethod
    def distributable(verifier=None):
        """
        Takes a function and converts it to a binary, the binary is then
        registered with the BinaryManager. The function is returned unchanged.
        """
        def distributable_decorator(function):
            Dipla._process_decorated_function(function, verifier)
            Dipla._task_creators[id(function)] = Dipla._create_normal_task
            return function

        return distributable_decorator

    @staticmethod
    def reduce_distributable(reduce_group_size=2):
        """Takes a function that should expect a single parameter of a list of
        values to reduce, and registers it with the BinaryManager."""

        def distributable_decorator(function):
            Dipla._task_creators[id(function)] = Dipla._create_normal_task
            Dipla._reduce_task_group_sizes[id(function)] = reduce_group_size
            return function

        return distributable_decorator
        

    @staticmethod
    def scoped_distributable(count, verifier=None):
        """
        Takes a function and converts it to a binary, the binary is then
        registered with the BinaryManager. The function is returned unchanged.

        This function must have parameters called `index` and `count` as
        the last two parameters which contain integer values for the
        current interval (index) out of the total number of intervals
        (count) for this function
        """
        # If no count is supplied then count will be a function. This is
        # not supported
        if callable(count):
            raise NotImplementedError(
                "Cannot create scoped distributable without providing a count")

        def _create_scoped_task(sources, task_instructions):
            """
            sources are objects that can be used to create a data
            source, e.g. an iterable or another task
            """

            def read_without_consuming(collection, current_location):
                return collection[0]

            def return_current_location(collection, current_location):
                return current_location

            def available_n_times(collection, current_location):
                return current_location < count

            def always_move_by_1(collection, current_location):
                return current_location + 1

            source_uids = []

            def create_data_source(source, data_source_creator):
                return data_source_creator(
                    source,
                    Dipla._generate_uid_in_list(source_uids),
                    read_without_consuming,
                    available_n_times,
                    always_move_by_1)

            task = Dipla._create_clientside_task(task_instructions)
            Dipla._add_sources_to_task(sources, task, create_data_source)

            task.add_data_source(DataSource.create_source_from_iterable(
                [0],
                Dipla._generate_uid_in_list(source_uids),
                return_current_location,
                available_n_times,
                always_move_by_1))

            task.add_data_source(DataSource.create_source_from_iterable(
                [count],
                Dipla._generate_uid_in_list(source_uids),
                read_without_consuming,
                available_n_times,
                always_move_by_1))

            return task

        def real_decorator(function):
            Dipla._task_creators[id(function)] = _create_scoped_task
            Dipla._process_decorated_function(function, verifier)
            return function
        return real_decorator

    @staticmethod
    def explorer():
        def real_decorator(function):
            def discovered_handler(task_uid, signal_inputs):
                Dipla.task_queue.push_task_input(task_uid, signal_inputs)

            signals = {
                "DISCOVERED": discovered_handler
            }
            Dipla._task_input_script_info[id(function)] =\
                (script_templates.explorer_argv_input_script, signals)
            return function
        return real_decorator

    @staticmethod
    def data_source(function):
        def read_function_wrapper(source, location):
            # Abstract the ability to return multiple results from the
            # user, always give them one input and expect one output.
            # Give them each value in the source and convert their
            # output to a single value array
            if len(source) > 0:
                return [function(source.pop(0))]
        return read_function_wrapper

    @staticmethod
    def _generate_task_id():
        return uid_generator.generate_uid(
            length=8, existing_uids=Dipla.task_queue.get_task_ids())

    @staticmethod
    def read_data_source(read_function, source):
        task_uid = Dipla._generate_task_id()
        # The Task name is only used to run binaries, which does not
        # happen when reading a data source, so we simply call this
        # 'read_data_source' as it is never used. This actually creates
        # a Task object from the provided read function, so we will add
        # it to the TaskQueue as a Server task
        read_task = Task(
            task_uid,
            'read_data_source',
            MachineType.server,
            complete_check=Dipla.complete_on_eof)
        source_uid = uid_generator.generate_uid(length=8, existing_uids=[])
        # Create a reader task that consumes the input source being read,
        # this does not move the location because consuming the values
        # will cause the read function to find new values anyway
        read_task.add_data_source(DataSource.create_source_from_iterable(
            source,
            source_uid,
            read_function,
            availability_check=Dipla.stream_not_empty,
            location_changer=lambda x, y: False))
        Dipla.task_queue.push_task(read_task)
        return Promise(task_uid)

    @staticmethod
    def apply_distributable(function, *raw_args):
        """
        Takes a distributable function, and any number of further arguments
        where each is a list of immediate values or a Promise of future values,
        and adds that function to the task queue.

        Params:
         - function: A function decorated with @Dipla.distributable, that the
        user wants to give some input to.
         - n further arguments, where each is a list of immediate values (eg.
        [1, 2, 3, 4, 5]) or a Promise of values (eg. result_of_other_func).

        Raises:
         - UnsupportedInput if an input is given to a function that is not one
        of the above mentioned types.

        Returns:
         - A Promise, which can be used later as the input to another task,
        or the user can await its results.
        """
        if id(function) not in Dipla._task_creators:
            raise KeyError("Provided function was not decorated using Dipla")

        is_reduce = id(function) in Dipla._reduce_task_group_sizes

        if is_reduce and len(raw_args) != 1:
            raise KeyError("Incorrect number of arguments given for reduce distributable")

        args = []
        for arg in raw_args:
            if isinstance(arg, Promise):
                args.append(Dipla.task_queue.get_task_by_id(arg.task_uid))
            elif isinstance(arg, list):
                args.append(arg)
            else:
                raise UnsupportedInput()
        function_id = id(function)
        task = None
        if is_reduce:
            print('creating reduce task')
            group_size = Dipla._reduce_task_group_sizes[id(function)]
            print('group size =', group_size)
            task = Dipla._task_creators[function_id](args,
                                                     function.__name__,
                                                     is_reduce=True,
                                                     reduce_group_size=group_size)
            print(args)
        else:
            task = Dipla._task_creators[function_id](args, function.__name__)

        if function_id in Dipla._task_input_script_info:
            task.signals = Dipla._task_input_script_info[function_id][1]
        Dipla.task_queue.push_task(task)
        return Promise(task.uid)

    @staticmethod
    def apply_reduce(function, arg):
        if id(function) not in Dipla._task_creators:
            raise KeyError("blah")

        args = None
        if isinstance(arg, Promise):
            args = [Dipla.task_queue.get_task_by_id(arg.task_uid)]
        elif isinstance(arg, list):
            args = [arg]
        else:
            raise UnsupportedInput()

        print(args)

        function_id = id(function)
        task = Dipla._task_creators[function_id](args, function.__name__, is_reduce=True)
        Dipla.task_queue.push_task(task)
        return Promise(task.uid)
        

    def _create_binary_manager():
        return BinaryManager()

    @staticmethod
    def _start_client_thread():
        config = ConfigHandler()
        if Dipla._password:
            config.add_param('password', Dipla._password)
        proc = Process(
            target=ClientFactory.create_and_run_client,
            args=(config,)
        )
        proc.start()
        return proc

    @staticmethod
    def get(promise, run_on_server=False):
        """Turns a promise into the immediate values by starting the server

        Args:
         - promise: Promise to get
         - run_on_server: Start a client alongside the server for debugging"""
        task_uid = Dipla._generate_task_id()

        # Get function is given a complete function so that the server
        # will terminate once it runs out of values
        get_task = Task(
            task_uid,
            'get',
            MachineType.server,
            complete_check=Dipla.complete_on_eof)
        # Generate a uid for the source (bridge) from the get task to
        # the task provided in the promise
        source_uid = uid_generator.generate_uid(length=8, existing_uids=[])
        get_task.add_data_source(DataSource.create_source_from_task(
            Dipla.task_queue.get_task(promise.task_uid), source_uid))
        Dipla.task_queue.push_task(get_task)

        binary_manager = Dipla._create_binary_manager()
        for function_id in Dipla._task_functions:
            input_template = (script_templates.argv_input_script, dict())
            if function_id in Dipla._task_input_script_info:
                input_template = Dipla._task_input_script_info[function_id]
            function = Dipla._task_functions[function_id]
            # Turn the function into a base64'd Python script.
            base64_binary = get_encoded_script(function, input_template[0])
            # Register the result as a new binary for any platform with the
            # name of the function as the task name.
            binary_manager.add_encoded_binaries('.*', [
                (function.__name__, base64_binary),
            ])

        server = Server(
            task_queue=Dipla.task_queue,
            services=ServerServices(
                binary_manager,
                Dipla.stat_updater),
            result_verifier=Dipla.result_verifier,
            stats=Dipla.stat_updater)

        if run_on_server:
            client = Dipla._start_client_thread()
            server.start(password=Dipla._password)
            client.terminate()
        else:
            server.start(password=Dipla._password)


        if Dipla.task_queue.get_task(promise.task_uid).is_reduce:
            # The task that has been requested is a reduce task,
            # so we only care about the very last value returned.
            return get_task.task_output[-1]
        else:
            return get_task.task_output

    @staticmethod
    def set_password(password):
        Dipla._password = password

    def start_dashboard(host='localhost', port=8080):
        """
        Start a webserver hosting a dashboard at the given host and port,
        in a new thread. This dashboard will give you some information
        on the current runtime status of the project, in human-readable
        format. It will be visible in the browser at http://host:port,
        depending on what host and port are given.

        This function will also install all the dependencies necessary
        for the dashboard, and transpile and pack the resources. The
        first time you run it, it will be very slow, as it has to
        download many files from NPM. However, on subsequent runs, it
        will take less than 5 seconds.

        Params:
         - host: A string specifiying the address the dashboard server
           will be run from. If the host is set to '0.0.0.0', the server
           will listen on all active IPs for the machine.
         - port: An integer specifying which port the server should
           listen on. If this number is below 1024, the OS will require
           root access in order to successfully bind the port. The port
           defaults to 8080.

        Raises:
         - PermissionError if the port specified is below 1024 and the
           program was not run with root access.
         - OSError if the port given is already being used by a different
           process.
        """
        stat_reader = statistics.StatisticsReader(Dipla._stats)
        dashboard = DashboardServer(host, port, stat_reader)
        dashboard.start()

    @staticmethod
    def inform_discovery_server(discovery_server_address,
                                project_address,
                                project_title,
                                project_description):
        """
        Give a discovery server at the provided address information about
        this project, and inform it that the project is accepting
        volunteers.

        Params:
        - discovery_server_address: A string with the fully resolvable
          location of the desired discovery server, eg. "http://example.com
        - project_address: A string with the fully resolvable location of
          this dipla server, that clients will be able to use to connect.
          It must have an explicit protocol, host, and port. For example,
          the string "http://example.com:9876" is valid, but the string
          "example.com" is not.
        - project_title: The title of this dipla project, that potential
          volunteers will see in the client when they are choosing a
          project to connect to.
        - project_description: Some more information about this dipla
          project, that volunteers will see in the client when they are
          connecting.

        Raises:
        - urllib.error.HTTPError if there was a problem in connecting
          with a discovery server at the given address.
        - DiscoveryConflict if a HTTP error 409 was received from the
          discovery server (eg. if there is already a project
          registered with that server at the given address).
        - DiscoveryBadRequest if a HTTP error 400 was received from the
          discovery server (eg. if the project address you gave was not
          fully resolvable)
        - RuntimeError if a different kind of error was received as a
          response from the discovery server.
        """
        full_address = '{}/add_server'.format(discovery_server_address)
        post_data = {
            'address': project_address,
            'title': project_title,
            'description': project_description,
        }
        request = Request(full_address,
                          urlencode(post_data).encode())
        raw_data = urlopen(request).read().decode()
        data = json.loads(raw_data)
        if not data['success']:
            error_msg = 'Received error from discovery server: "{}"'
            if '409' in data['error']:
                raise DiscoveryConflict(error_msg.format(data['error']))
            elif '400' in data['error']:
                raise DiscoveryBadRequest(error_msg.format(data['error']))
            else:
                raise RuntimeError(error_msg.format(data['error']))


class Promise:

    def __init__(self, promise_uid):
        self.task_uid = promise_uid

    def distribute(self, function, *args):
        return Dipla.apply_distributable(
            function, *([self] + [x for x in args]))

    def get(self, run_on_server=False):
        """Get the immediate value of this promise by starting the server

        If run_on_server is true then a client will be started on the
        server to help with debugging."""
        return Dipla.get(self, run_on_server)


class UnsupportedInput(Exception):
    """
    An exception that is raised when an input of an unsupported type is
    applied to a distributable
    """
    pass


class DiscoveryConflict(RuntimeError):
    """
    An exception that is raied when the discovery server returns a http
    409 error
    """
    pass


class DiscoveryBadRequest(RuntimeError):
    """
    An exception that is raised when the discovery server returns a http
    400 error
    """
    pass


# Remember that the function's __name__ is the task name in apply_distributable
# task_name = function.__name__

# When starting the server inside this class you must inject the binary
# manager that's tied to the class. Eg:
# Dipla.server = Server(
#     Dipla.tq,
#     Dipla.binary_manager
# )
