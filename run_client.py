from client.quality_scorer import QualityScorer
from dipla.client.client import Client, ClientEventListener
from dipla.client.config_handler import ConfigHandler
from dipla.client.client_services import RunInstructionsService
from dipla.client.client_services import VerifyInputsService
from dipla.client.client_services import BinaryReceiverService
from dipla.client.client_services import ServerErrorService
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.shared.logutils import LogUtils
from dipla.shared.network.network_connection import ClientConnection
from logging import FileHandler
from argparse import ArgumentParser


def main():
    parser = ArgumentParser(description="Start a Dipla client.")
    parser.add_argument('-c', default='', dest='config_path')
    args = parser.parse_args()

    config = ConfigHandler()
    if args.config_path:
        config.parse_from_file(args.config_path)

    init_logger(config.params['log_file'])

    password = config.params['password']
    server_ip = config.params['server_ip']
    server_port = config.params['server_port']

    services = create_services()
    event_listener = ClientEventListener(services)
    connection = ClientConnection(server_ip, server_port, event_listener)
    quality_scorer = QualityScorer()

    client = Client(
        event_listener,
        connection,
        quality_scorer,
        password
    )

    client.start()


def init_logger(loc):
    LogUtils.init(handler=FileHandler(loc))


def create_services():
    binary_paths = {}
    binary_runner = CommandLineBinaryRunner()
    binary_base_file_path = './'
    services = {
        RunInstructionsService.get_label(): RunInstructionsService(
            binary_paths,
            binary_runner
        ),
        VerifyInputsService.get_label(): VerifyInputsService(
            binary_paths,
            binary_runner
        ),
        BinaryReceiverService.get_label(): BinaryReceiverService(
            binary_base_file_path,
            binary_paths
        ),
        ServerErrorService.get_label(): ServerErrorService()
    }
    return services


if __name__ == '__main__':
    main()
