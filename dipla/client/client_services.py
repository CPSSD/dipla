

class BinaryRunnerService(object):

    def __init__(self, binary_runner):
        self._binary_runner = binary_runner

    def execute(self, json_data):
        filepath = json_data["filepath"]
        arguments = json_data["arguments"]
        self._binary_runner.run(filepath, arguments)
