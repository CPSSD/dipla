from dipla.client.client import Client
from dipla.client.client_services import BinaryRunnerService
from dipla.client.client_services import BinaryReceiverService
from dipla.client.client_services import ServerErrorService
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.shared import logutils
import sys
from logging import FileHandler


def main(argv):
    init_logger(argv)
    if len(argv) > 1:
        server_address = argv[1]
        # Allow addresses to be specified without port
        if not server_address.endswith('8765'):
            server_address += ':8765'
    else:
        server_address = 'localhost:8765'
    client = Client('ws://{}'.format(server_address))
    services = create_services(client)
    client.inject_services(services)
    client.start()


def init_logger(argv):
    loc = 'DIPLA.log'
    if len(argv) == 2:
        loc = argv[1]
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
