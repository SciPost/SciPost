__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.utils import ProgrammingError


class JournalDOILabelConverter:
    def __init__(self):
        try:
            from journals.models import Journal

            self.regex = "|".join([j.doi_label for j in Journal.objects.all()])
        except ProgrammingError:
            self.regex = "SciPost"

    def to_python(self, value):
        from journals.models import Journal

        try:
            return Journal.objects.get(doi_label=value).doi_label
        except Journal.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value


class IssueDOILabelConverter:
    """
    Converter for journal issue DOI labels.
    """

    def __init__(self):
        try:
            from journals.models import Journal

            self.regex = "|".join([j.doi_label for j in Journal.objects.all()])
        except ProgrammingError:
            self.regex = "SciPost"
        self.regex = "(" + self.regex + ")" + r"\.[0-9]+(\.[0-9]+)?"

    def to_python(self, value):
        from journals.models import Publication

        try:
            return Publication.objects.get(doi_label=value).doi_label
        except Publication.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value


class PublicationDOILabelConverter:
    """
    Converter for publication DOI labels.
    """

    def __init__(self):
        try:
            from journals.models import Journal

            self.regex = "|".join([j.doi_label for j in Journal.objects.all()])
        except ProgrammingError:
            self.regex = "SciPost"
        self.regex = (
            "("
            + self.regex
            + ")"
            + r"\.[0-9]+(\.[0-9]+(\.[0-9]+)?)?(-r[0-9]+(\.[0-9]+)?)?"
        )

    def to_python(self, value):
        from journals.models import Publication

        try:
            return Publication.objects.get(doi_label=value).doi_label
        except Publication.DoesNotExist:
            return ValueError
        return value

    def to_url(self, value):
        return value
