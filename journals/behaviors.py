__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import RegexValidator

#from .regexes import PUBLICATION_DOI_VALIDATION_REGEX


doi_journal_validator = RegexValidator(
    r'^[a-zA-Z]+$', 'Only valid DOI expressions are allowed ([a-zA-Z]+).')
doi_volume_validator = RegexValidator(
    r'^[a-zA-Z]+.[0-9]+$', 'Only valid DOI expressions are allowed ([a-zA-Z]+.[0-9]+).')
doi_issue_validator = RegexValidator(
    r'^[a-zA-Z]+.\w+(.[0-9]+)?$',
    'Only valid DOI expressions are allowed ([a-zA-Z]+.\w+(.[0-9]+)?)')
doi_publication_validator = RegexValidator(
    r'[a-zA-Z]+(.\w+(.[0-9]+(.[0-9]{3,})?)?)?',
    #r'^{regex}$'.format(regex=PUBLICATION_DOI_VALIDATION_REGEX),
    'Only valid DOI expressions are allowed: `[a-zA-Z]+(.\w+(.[0-9]+(.[0-9]{3,})?)?)?`')
