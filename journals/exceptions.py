class JournalNameError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


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
