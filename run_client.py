from dipla.client.client import Client
from dipla.client.config_handler import ConfigHandler
from dipla.client.client_services import RunInstructionsService
from dipla.client.client_services import VerifyInputsService
from dipla.client.client_services import BinaryReceiverService
from dipla.client.client_services import ServerErrorService
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.shared.logutils import LogUtils
from dipla.shared.statistics import StatisticsUpdater
import sys
import argparse
from logging import FileHandler

TK_AVAILABLE = True
try:
    from dipla.client.ui import DiplaClientUI
except ImportError:
    TK_AVAILABLE = False



def main(argv):
    parser = argparse.ArgumentParser(description="Start a Dipla client.")
    parser.add_argument('-c', default='', dest='config_path',
                        help="Optional path to a JSON config file")
    parser.add_argument('--ui', action="store_true",
                        help="Use the Dipla Client UI")
    args = parser.parse_args()

    config = ConfigHandler()

    if args.config_path:
        config.parse_from_file(args.config_path)

    if args.ui and TK_AVAILABLE:
        ui = DiplaClientUI(
            config=config,
            client_creator=create_and_run_client,
            stats_creator=create_default_client_stats)
        ui.run()
    else:
        stats = create_default_client_stats()
        create_and_run_client(config, stats)

def create_default_client_stats():
    return {
        'processing_time': 0.0,
        'requests_resolved': 0,
        'tasks_done': 0,
        'messages_sent': 0,
        'running': False
    }

def create_and_run_client(config, stats):
    init_logger(config.params['log_file'])
    client = Client(
        stats=StatisticsUpdater(stats)
    )
    services = create_services(client)
    client.inject_services(services)
    client.start(
        server_address='ws://{}:{}'.format(
            config.params['server_ip'], config.params['server_port']),
        password=config.params['password']
    )


def init_logger(loc):
    LogUtils.init(handler=FileHandler(loc))


def create_services(client):
    services = {
        RunInstructionsService.get_label():
            _create_run_instructions_service(client),
        VerifyInputsService.get_label(): _create_verify_inputs_service(client),
        BinaryReceiverService.get_label(): _create_binary_receiver(client),
        ServerErrorService.get_label(): ServerErrorService(client)
    }
    return services


def _create_run_instructions_service(client):
    binary_runner = CommandLineBinaryRunner()
    return RunInstructionsService(client, binary_runner)


def _create_verify_inputs_service(client):
    binary_runner = CommandLineBinaryRunner()
    return VerifyInputsService(client, binary_runner)


def _create_binary_receiver(client):
    return BinaryReceiverService(client, './binary')


if __name__ == '__main__':
    main(sys.argv)
