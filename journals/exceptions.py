__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class PaperNumberError(Exception):
    def __init__(self, nr):
        self.nr = nr

    def __str__(self):
        return self.nr


class PaperNumberingError(Exception):
    def __init__(self, nr):
        self.nr = nr

    def __str__(self):
        return self.nr


class InvalidDOIError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
