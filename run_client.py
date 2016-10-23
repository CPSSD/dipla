from dipla.client.client import Client
from dipla.shared import logutils
import sys
from logging import FileHandler

if __name__ == '__main__':
    logutils.init()
    loc = 'DIPLA.log'
    if len(sys.argv) == 2:
        loc = sys.argv[1]
    c = Client('ws://localhost:8765')
    c.start()
