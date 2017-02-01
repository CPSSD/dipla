from dipla.client.client import Client
from dipla.client.config_handler import ConfigHandler
from dipla.client.client_services import BinaryRunnerService
from dipla.client.client_services import BinaryReceiverService
from dipla.client.client_services import ServerErrorService
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.shared import logutils
import sys
import argparse
from logging import FileHandler


def main(argv):
    parser = argparse.ArgumentParser(description="Start a Dipla client.")
    parser.add_argument('-c', default='', dest='config_path')
    args = parser.parse_args()

    config = ConfigHandler()
    if args.config_path:
        config.parse_from_file(args.config_path)

    init_logger(config.params['log_file'])

    client = Client('ws://{}:{}'.format(
        config.params['server_ip'], config.params['server_port']))
    services = create_services(client)
    client.inject_services(services)
    client.start()


def init_logger(loc):
    logutils.init(handler=FileHandler(loc))


def create_services(client):
    services = {
        BinaryRunnerService.get_label(): _create_binary_runner(client),
        BinaryReceiverService.get_label(): _create_binary_receiver(client),
        ServerErrorService.get_label(): ServerErrorService(client)
    }
    return services


def _create_binary_runner(client):
    binary_runner = CommandLineBinaryRunner()
    return BinaryRunnerService(client, binary_runner)


def _create_binary_receiver(client):
    return BinaryReceiverService(client, './binary')


if __name__ == '__main__':
    main(sys.argv)
