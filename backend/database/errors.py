class NotFoundException(Exception):
    code = 404

    def __init__(self, message):
        super().__init__(message)
        self.description = message


class AlreadyExistsException(Exception):
    code = 400

    def __init__(self, message):
        super().__init__(message)
        self.description = message
