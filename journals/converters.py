__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.utils import ProgrammingError


class JournalDOILabelConverter:

    def __init__(self):
        try:
            from journals.models import Journal
            self.regex = '|'.join([j.doi_label for j in Journal.objects.all()])
        except ProgrammingError:
            self.regex = 'SciPost'

    def to_python(self, value):
        from journals.models import Journal
        try:
            return Journal.objects.get(doi_label=value).doi_label
        except Journal.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
