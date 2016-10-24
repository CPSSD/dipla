from dipla.client.client import Client
from dipla.client.client_services import BinaryRunnerService
from dipla.shared import logutils
import sys
from logging import FileHandler


def main(argv):
    init_logger(argv)
    client = Client('ws://localhost:8765')
    services = create_services(client)
    client.inject_services(services)
    client.start()


def init_logger(argv):
    loc = 'DIPLA.log'
    if len(argv) == 2:
        loc = argv[1]
    logutils.init(handler=FileHandler(loc))


def create_services(client):
    services = {"run_binary": _create_binary_runner_service(client)}
    return services


def _create_binary_runner_service(client):
    binary_runner = CommandLineBinaryRunner()
    return BinaryRunnerService(client, binary_runner)


if __name__ == '__main__':
    main(sys.argv)
