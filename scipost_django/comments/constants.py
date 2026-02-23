__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


EXTENTIONS_IMAGES = [".jpg", ".png"]
EXTENTIONS_PDF = [".pdf"]
EXTENTIONS_FILES = EXTENTIONS_PDF + EXTENTIONS_IMAGES

STATUS_VETTED = 1
STATUS_PENDING = 0
STATUS_UNCLEAR = -1
STATUS_INCORRECT = -2
STATUS_NOT_USEFUL = -3
STATUS_DUPLICATE = -4
COMMENT_STATUS = (
    (STATUS_VETTED, "Vetted"),
    (STATUS_PENDING, "Not yet vetted (pending)"),
    (STATUS_UNCLEAR, "Rejected (unclear)"),
    (STATUS_INCORRECT, "Rejected (incorrect)"),
    (STATUS_NOT_USEFUL, "Rejected (not useful)"),
    (STATUS_DUPLICATE, "Rejected (duplicate)"),
)

COMMENT_CATEGORIES = (
    ("ERR", "erratum"),
    ("REM", "remark"),
    ("QUE", "question"),
    ("ANS", "answer to question"),
    ("OBJ", "objection"),
    ("REP", "reply to objection"),
    ("VAL", "validation or rederivation"),
    ("LIT", "pointer to related literature"),
    ("SUG", "suggestion for further work"),
)

COMMENT_ACTION_ACCEPT = 1
COMMENT_ACTION_REFUSE = 2
COMMENT_ACTION_CHOICES = (
    (COMMENT_ACTION_ACCEPT, "accept"),
    (COMMENT_ACTION_REFUSE, "refuse (give reason below)"),
)

COMMENT_REFUSAL_EMPTY = 0
COMMENT_REFUSAL_CHOICES = (
    (COMMENT_REFUSAL_EMPTY, "-"),
    (STATUS_UNCLEAR, "unclear"),
    (STATUS_INCORRECT, "incorrect"),
    (STATUS_NOT_USEFUL, "not useful"),
    (STATUS_DUPLICATE, "duplicate"),
)
