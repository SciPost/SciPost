__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.utils import ProgrammingError

def get_journal_doi_label_converter_regex():
    """
    Helper function to prevent migrations from crashing.
    """
    from journals.models import Journal
    try:
        return '|'.join([j.doi_label for j in Journal.objects.all()])
    except ProgrammingError:
        return 'SciPostPhys'


class JournalDOILabelConverter:
    regex = get_journal_doi_label_converter_regex()

    def to_python(self, value):
        from journals.models import Journal
        try:
            return Journal.objects.get(doi_label=value).doi_label
        except Journal.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
