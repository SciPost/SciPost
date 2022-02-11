__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class ConfigurationError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Configuration error: {}".format(self.name)
