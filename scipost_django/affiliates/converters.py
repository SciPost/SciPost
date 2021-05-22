__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import StringConverter

from .regexes import DOI_AFFILIATEPUBLICATION_REGEX


class Crossref_DOI_converter(StringConverter):
    regex = DOI_AFFILIATEPUBLICATION_REGEX
