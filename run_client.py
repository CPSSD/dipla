from dipla.client.client_factory import ClientFactory
from dipla.client.config_handler import ConfigHandler
import sys
import argparse

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

    if args.ui:
        if not TK_AVAILABLE:
            print("Please install tkinter to use UI")
            sys.exit(1)
        ui = DiplaClientUI(
            config=config,
            client_creator=ClientFactory.create_and_run_client,
            stats_creator=ClientFactory.create_default_client_stats)
        ui.run()
    else:
        ClientFactory.create_and_run_client(config)

if __name__ == '__main__':
    main(sys.argv)
