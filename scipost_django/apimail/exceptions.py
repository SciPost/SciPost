__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class APIMailError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "API Mail error: {}".format(self.name)
