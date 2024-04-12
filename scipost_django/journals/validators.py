__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import RegexValidator

from .regexes import (
    JOURNAL_DOI_LABEL_REGEX,
    VOLUME_DOI_LABEL_REGEX,
    ISSUE_DOI_LABEL_REGEX,
    PUBLICATION_DOI_LABEL_REGEX,
    CROSSREF_DOI_REGEX,
)

doi_journal_validator = RegexValidator(
    r"^{regex}$".format(regex=JOURNAL_DOI_LABEL_REGEX),
    "Only expressions with regex %s are allowed." % JOURNAL_DOI_LABEL_REGEX,
)
doi_volume_validator = RegexValidator(
    r"^{regex}$".format(regex=VOLUME_DOI_LABEL_REGEX),
    "Only expressions with regex %s are allowed." % VOLUME_DOI_LABEL_REGEX,
)
doi_issue_validator = RegexValidator(
    r"^{regex}$".format(regex=ISSUE_DOI_LABEL_REGEX),
    "Only expressions with regex %s are allowed." % ISSUE_DOI_LABEL_REGEX,
)
doi_publication_validator = RegexValidator(
    r"^{regex}$".format(regex=PUBLICATION_DOI_LABEL_REGEX),
    "Only expressions with regex %s are allowed." % PUBLICATION_DOI_LABEL_REGEX,
)
doi_validator = RegexValidator(
    r"^{regex}$".format(regex=CROSSREF_DOI_REGEX),
    "Only expressions with regex %s are allowed." % CROSSREF_DOI_REGEX,
)
