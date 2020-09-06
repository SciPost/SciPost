__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .regexes import ACADEMIC_FIELD_REGEX

class AcademicFieldConverter:
    regex = ACADEMIC_FIELD_REGEX

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
