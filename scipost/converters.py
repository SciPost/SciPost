__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .constants import DISCIPLINES_REGEX

class DisciplineConverter:
    regex = DISCIPLINES_REGEX

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
