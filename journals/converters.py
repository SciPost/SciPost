__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .regexes import JOURNAL_DOI_LABEL_REGEX

class JournalDOILabelConverter:
    regex = JOURNAL_DOI_LABEL_REGEX

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
