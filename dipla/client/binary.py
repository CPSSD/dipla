import os


class BinaryRunner(object):

    def __init__(self):
        pass

    def run(self, filepath):
        print(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError

