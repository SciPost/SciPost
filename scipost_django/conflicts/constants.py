__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


STATUS_UNVERIFIED, STATUS_VERIFIED = "unverified", "verified"
STATUS_DEPRECATED = "deprecated"
CONFLICT_OF_INTEREST_STATUSES = (
    (STATUS_UNVERIFIED, "Unverified"),
    (STATUS_VERIFIED, "Verified by Admin"),  # Confirmed // rejected
    (STATUS_DEPRECATED, "Deprecated"),
)


TYPE_OTHER, TYPE_COAUTHOR = "other", "coauthor"
CONFLICT_OF_INTEREST_TYPES = (
    (TYPE_COAUTHOR, "Co-authorship"),
    (TYPE_OTHER, "Other"),
)
