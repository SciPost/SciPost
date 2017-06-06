class CycleUpdateDeadlineError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class InvalidReportVettingValue(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
