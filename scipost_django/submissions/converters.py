__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import StringConverter

from .regexes import IDENTIFIER_REGEX


class IdentifierConverter(StringConverter):
    regex = IDENTIFIER_REGEX
