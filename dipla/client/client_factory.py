from dipla.client.client import Client
from dipla.client.client_services import RunInstructionsService
from dipla.client.client_services import VerifyInputsService
from dipla.client.client_services import BinaryReceiverService
from dipla.client.client_services import ServerErrorService
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.shared.logutils import LogUtils
from dipla.shared.statistics import StatisticsUpdater
from logging import FileHandler


class ClientFactory:

    @staticmethod
    def create_default_client_stats():
        return {
            'processing_time': 0.0,
            'requests_resolved': 0,
            'tasks_done': 0,
            'messages_sent': 0,
            'running': False
        }

    @staticmethod
    def create_and_run_client(config, stats=None):
        stats = stats or ClientFactory.create_default_client_stats()
        ClientFactory.init_logger(config.params['log_file'])
        client = Client(
            stats=StatisticsUpdater(stats)
        )
        services = ClientFactory.create_services(client)
        client.inject_services(services)
        client.start(
            server_address='ws://{}:{}'.format(
                config.params['server_ip'], config.params['server_port']),
            password=config.params['password']
        )

    @staticmethod
    def init_logger(loc):
        LogUtils.init(handler=FileHandler(loc))

    @staticmethod
    def create_services(client):
        services = {
            RunInstructionsService.get_label():
                ClientFactory._create_run_instructions_service(client),
            VerifyInputsService.get_label():
                ClientFactory._create_verify_inputs_service(client),
            BinaryReceiverService.get_label():
                ClientFactory._create_binary_receiver(client),
            ServerErrorService.get_label(): ServerErrorService(client)
        }
        return services

    @staticmethod
    def _create_run_instructions_service(client):
        binary_runner = CommandLineBinaryRunner()
        return RunInstructionsService(client, binary_runner)

    @staticmethod
    def _create_verify_inputs_service(client):
        binary_runner = CommandLineBinaryRunner()
        return VerifyInputsService(client, binary_runner)

    @staticmethod
    def _create_binary_receiver(client):
        return BinaryReceiverService(client, './binary')
