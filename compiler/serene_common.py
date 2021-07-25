import sys

def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class SereneScopeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SereneTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)