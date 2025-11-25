__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re


JOURNAL_DOI_LABEL_REGEX = r"(SciPost[a-zA-Z]+|MigPol|JRobustRep)"

VOLUME_DOI_LABEL_REGEX = r"({})\.\w+".format(JOURNAL_DOI_LABEL_REGEX)

ISSUE_DOI_LABEL_REGEX = r"({})\.\w+(\.[0-9]+)?".format(JOURNAL_DOI_LABEL_REGEX)

DOI_DISPATCH_PATTERN = (
    r"(?P<journal_tag>{})".format(JOURNAL_DOI_LABEL_REGEX)
    + r"(\.(?P<part_1>\w+)"  #! Why words and not just digits?
    + r"(\.(?P<part_2>\d+)"  # Any number of digits
    + r"(\.(?P<part_3>\d{3,})"  # At least 3 digits
    + r")?)?)?"  # Each part is nested in the previous one and optional
    + r"(-(?P<suffix>{}))?".format(  # Suffix can have multiple formats
        "|".join(
            [
                r"[rv]\d+(\.\d+)?",  # Code base releases/article versions r###.### or v###.###
                r"\w+",  # Other word suffixes (no dots)
            ]
        )
    )
)

# Remove the named groups from the regex, keep the rest intact
PUBLICATION_DOI_LABEL_REGEX = re.sub(r"\?P<[^>]+>", "", DOI_DISPATCH_PATTERN)

CROSSREF_DOI_REGEX = r"^10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$"
