class BaseCustomException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class CycleUpdateDeadlineError(BaseCustomException):
    pass


class InvalidReportVettingValue(BaseCustomException):
    pass
