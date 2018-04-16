__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class BaseCustomException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class CycleUpdateDeadlineError(BaseCustomException):
    pass


class InvalidReportVettingValue(BaseCustomException):
    pass


class ArxivPDFNotFound(Exception):
    pass


class InvalidDocumentError(Exception):
    pass
