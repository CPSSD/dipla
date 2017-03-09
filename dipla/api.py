from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dipla.api_support.function_serialise import get_encoded_script
from dipla.server.dashboard import DashboardServer
from dipla.server.result_verifier import ResultVerifier
from dipla.server.server import BinaryManager, Server, ServerServices
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.shared import uid_generator, statistics


class Dipla:

    # BinaryManager, TaskQueue and ResultVerifier to be injected into server.
    binary_manager = BinaryManager()
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

    def _create_clientside_task(task_instructions):
        task_uid = uid_generator.generate_uid(
            length=8,
            existing_uids=Dipla.task_queue.get_task_ids())
        return Task(
            task_uid,
            task_instructions,
            MachineType.client,
            complete_check=Dipla.complete_when_unavailable)

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

    def _create_normal_task(sources, task_instructions):
        """
        sources are objects that can be used to create a data source,
        e.g. an iterable or another task
        """
        task = Dipla._create_clientside_task(task_instructions)

        source_uids = []

        def create_default_data_source(source, data_source_creator):
            return data_source_creator(source, source_uids)

        Dipla._add_sources_to_task(sources, task, create_default_data_source)
        return task

    def _process_decorated_function(function, verifier=None):
        # Turn the function into a base64'd Python script.
        base64_binary = get_encoded_script(function)
        # Register the result as a new binary for any platform with the
        # name of the function as the task name.
        Dipla.binary_manager.add_encoded_binaries('.*', [
            (function.__name__, base64_binary),
        ])
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

        args = []
        for arg in raw_args:
            if isinstance(arg, Promise):
                args.append(Dipla.task_queue.get_task_by_id(arg.task_uid))
            elif isinstance(arg, list):
                args.append(arg)
            else:
                raise UnsupportedInput()
        task = Dipla._task_creators[id(function)](args, function.__name__)
        Dipla.task_queue.push_task(task)
        return Promise(task.uid)

    @staticmethod
    def get(promise):
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

        server = Server(
            task_queue=Dipla.task_queue,
            services=ServerServices(
                Dipla.binary_manager,
                Dipla.stat_updater),
            result_verifier=Dipla.result_verifier,
            stats=Dipla.stat_updater)
        server.start(password=Dipla._password)

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
        post_data = {
            'address': project_address,
            'title': project_title,
            'description': project_description,
        }
        request = Request(discovery_server_address,
                          urlencode(post_data).encode())
        json = urlopen(request).read().decode()
        data = json.loads(json)
        if not data['success']:
            pass


class Promise:

    def __init__(self, promise_uid):
        self.task_uid = promise_uid


class UnsupportedInput(Exception):
    """
    An exception that is raised when an input of an unsupported type is
    applied to a distributable
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
