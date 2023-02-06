__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class BaseCustomException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class StageNotDefinedError(BaseCustomException):
    pass


class CycleUpdateDeadlineError(BaseCustomException):
    pass


class InvalidReportVettingValue(BaseCustomException):
    pass


class PreprintDocumentNotFoundError(BaseCustomException):
    pass


class ArxivPDFNotFound(Exception):
    pass


class InvalidDocumentError(Exception):
    pass
