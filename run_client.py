from dipla.client.client import Client
from dipla.shared import logutils
import sys
from logging import FileHandler

if __name__ == '__main__':
    loc = 'DIPLA.log'
    if len(sys.argv) == 2:
        loc = sys.argv[1]
    logutils.init(handler=FileHandler(loc))
    c = Client('ws://localhost:8765')
    c.start()
