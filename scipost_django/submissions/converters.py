__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import StringConverter

from .regexes import IDENTIFIER_WO_VN_NR_REGEX, IDENTIFIER_REGEX


class IdentifierWithoutVersionNumberConverter(StringConverter):
    regex = IDENTIFIER_WO_VN_NR_REGEX


class IdentifierConverter(StringConverter):
    regex = IDENTIFIER_REGEX


class ReportDOILabelConverter:
    regex = r"^(10.21468/)?SciPost.Report.[0-9]+"

    def to_python(self, value):
        """Strip the DOI prefix if present; check if Comment exists."""
        doi_label = value
        if doi_label.startswith("10.21468/"):
            doi_label = doi_label.partition("10.21468/")[2]
        from submissions.models import Report

        try:
            return Report.objects.get(doi_label=doi_label).doi_label
        except Report.DoesNotExist:
            return ValueError
        return doi_label

    def to_url(self, value):
        return value
