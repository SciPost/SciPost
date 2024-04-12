__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


JOURNAL_DOI_LABEL_REGEX = r"(SciPost)[a-zA-Z]+|(MigPol)"

VOLUME_DOI_LABEL_REGEX = r"({})\.\w".format(JOURNAL_DOI_LABEL_REGEX)

ISSUE_DOI_LABEL_REGEX = r"({})\.\w+(\.[0-9]+)?".format(JOURNAL_DOI_LABEL_REGEX)

PUBLICATION_DOI_LABEL_REGEX = r"({})".format(JOURNAL_DOI_LABEL_REGEX)
PUBLICATION_DOI_LABEL_REGEX += (
    r"(\.\w+(\.[0-9]+(\.[0-9]{3,})?)?)?(-r[0-9]+(\.[0-9]+)?)?"
)

DOI_DISPATCH_PATTERN = r"(?P<journal_tag>{})".format(JOURNAL_DOI_LABEL_REGEX)
DOI_DISPATCH_PATTERN += r"(\.(?P<part_1>\w+)(\.(?P<part_2>[0-9]+)(\.(?P<part_3>[0-9]{3,}))?)?)?(-(?P<suffix>[0-9]+(\.[0-9]+)?))?"

CROSSREF_DOI_REGEX = r"^10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$"
