class ServiceError(RuntimeError):

    def __init__(self, message, code):
        super(ServiceError, self).__init__(message)
        self.code = code
