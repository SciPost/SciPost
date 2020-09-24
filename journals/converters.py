__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import StringConverter

from journals.models import Journal


class JournalDOILabelConverter(StringConverter):

    def to_python(self, value):
        try:
            return Journal.objects.get(doi_label=value).doi_label
        except Journal.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
