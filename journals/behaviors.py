from django.core.validators import RegexValidator

doi_journal_validator = RegexValidator(r'^[a-zA-Z]+$',
                                       'Only valid DOI expressions are allowed ([a-zA-Z]+).')
doi_volume_validator = RegexValidator(r'^[a-zA-Z]+.[0-9]+$',
                                      'Only valid DOI expressions are allowed ([a-zA-Z]+.[0-9]+).')
doi_issue_validator = RegexValidator(r'^[a-zA-Z]+.[0-9]+.[0-9]+$',
                                     ('Only valid DOI expressions are allowed '
                                      '([a-zA-Z]+.[0-9]+.[0-9]+).'))
doi_publication_validator = RegexValidator(r'^[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,}$',
                                           ('Only valid DOI expressions are allowed '
                                            '([a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,}).'))
