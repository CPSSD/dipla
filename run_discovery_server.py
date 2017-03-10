import argparse
from dipla.discovery_server.app import DiscoveryServer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start a discovery server.")
    parser.add_argument('--host',
                        type=str,
                        default='0.0.0.0',
                        help="The address of the server (default=0.0.0.0)")
    parser.add_argument('--port',
                        type=int,
                        default=8766,
                        help="The port of the server (default=8766)")
    args = parser.parse_args()
    app = DiscoveryServer(host=args.host, port=args.port)
    app.start()
