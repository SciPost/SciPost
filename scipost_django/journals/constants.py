__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


STATUS_DRAFT = "draft"
STATUS_PUBLICLY_OPEN = "publicly_open"
STATUS_PUBLISHED = "published"
ISSUE_STATUSES = (
    (STATUS_DRAFT, "Draft"),
    (STATUS_PUBLICLY_OPEN, "Publicly open"),
    (STATUS_PUBLISHED, "Published"),
)

PUBLICATION_PREPUBLISHED, PUBLICATION_PUBLISHED = ("prepub", "pub")
PUBLICATION_STATUSES = (
    (STATUS_DRAFT, "Draft"),
    (PUBLICATION_PREPUBLISHED, "Pre-published"),
    (PUBLICATION_PUBLISHED, "Published"),
)

CCBY4 = "CC BY 4.0"
CCBYSA4 = "CC BY-SA 4.0"
CCBYNC4 = "CC BY-NC 4.0"
CC_LICENSES = (
    (CCBY4, "CC BY (4.0)"),
    (CCBYSA4, "CC BY-SA (4.0)"),
    (CCBYNC4, "CC BY-NC (4.0)"),
)

CC_LICENSES_URI = (
    (CCBY4, "https://creativecommons.org/licenses/by/4.0"),
    (CCBYSA4, "https://creativecommons.org/licenses/by-sa/4.0"),
    (CCBYNC4, "https://creativecommons.org/licenses/by-nc/4.0"),
)


ISSUES_AND_VOLUMES = "IV"
ISSUES_ONLY = "IO"
INDIVIDUAL_PUBLICATIONS = "IP"
JOURNAL_STRUCTURE = (
    (ISSUES_AND_VOLUMES, "Issues and Volumes"),
    (ISSUES_ONLY, "Issues only"),
    (INDIVIDUAL_PUBLICATIONS, "Individual Publications"),
)
