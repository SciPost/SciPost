__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import RegexValidator

from .regexes import DOI_AFFILIATEPUBLICATION_REGEX


doi_affiliatepublication_validator = RegexValidator(
    r'^{regex}$'.format(regex=DOI_AFFILIATEPUBLICATION_REGEX),
    'Only expressions with regex %s are allowed.' % DOI_AFFILIATEPUBLICATION_REGEX)
