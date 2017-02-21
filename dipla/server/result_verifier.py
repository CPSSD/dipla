class ResultVerifier:
    def __init__(self):
        self._verifiers = {}

    def add_verifier(self, task_name, func):
        if func.__code__.co_argcount != 2:
            raise ValueError("Verification function must take 2 arguments")
        self._verifiers[task_name] = func

    def verify_output_correct(self, task_name, inputs, outputs):
        if task_name in self._verifiers:
            return self._verifiers[task_name](inputs, outputs)
        return True
