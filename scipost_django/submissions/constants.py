__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


ED_COMM_CHOICES = (
    ("EtoA", "Editor-in-charge to Author"),
    ("EtoR", "Editor-in-charge to Referee"),
    ("EtoS", "Editor-in-charge to SciPost Editorial Administration"),
    ("AtoE", "Author to Editor-in-charge"),
    ("RtoE", "Referee to Editor-in-charge"),
    ("StoE", "SciPost Editorial Administration to Editor-in-charge"),
)

REFEREE_QUALIFICATION = (
    (None, "-"),
    (4, "expert in this subject"),
    (3, "very knowledgeable in this subject"),
    (2, "knowledgeable in this subject"),
    (1, "generally qualified"),
    (0, "not qualified"),
)

QUALITY_SPEC = (
    (None, "-"),
    (6, "perfect"),
    (5, "excellent"),
    (4, "good"),
    (3, "reasonable"),
    (2, "acceptable"),
    (1, "below threshold"),
    (0, "mediocre"),
)

# Only values between 0 and 100 are kept, anything outside those limits is discarded.
RANKING_CHOICES = (
    (None, "-"),
    (100, "top"),
    (80, "high"),
    (60, "good"),
    (40, "ok"),
    (20, "low"),
    (0, "poor"),
)

REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3 = 1, 2, 3
REPORT_MINOR_REV, REPORT_MAJOR_REV = -1, -2
REPORT_REJECT = -3
REPORT_ALT_JOURNAL = -4
REPORT_REC = (
    (None, "-"),
    (
        REPORT_PUBLISH_1,
        "Publish (surpasses expectations and criteria for this Journal; among top 10%)",
    ),
    (
        REPORT_PUBLISH_2,
        "Publish (easily meets expectations and criteria for this Journal; among top 50%)",
    ),
    (REPORT_PUBLISH_3, "Publish (meets expectations and criteria for this Journal)"),
    (REPORT_MINOR_REV, "Ask for minor revision"),
    (REPORT_MAJOR_REV, "Ask for major revision"),
    (REPORT_ALT_JOURNAL, "Accept in alternative Journal (see Report)"),
    (REPORT_REJECT, "Reject"),
)

#
# Reports
#
REPORT_ACTION_ACCEPT = "accept"
REPORT_ACTION_REFUSE = "refuse"
REPORT_ACTION_CHOICES = (
    (REPORT_ACTION_ACCEPT, "accept"),
    (REPORT_ACTION_REFUSE, "refuse"),
)

STATUS_DRAFT = "draft"
STATUS_VETTED = "vetted"
STATUS_UNVETTED = "unvetted"
STATUS_UNCLEAR = "unclear"
STATUS_INCORRECT = "incorrect"
STATUS_NOT_USEFUL = "notuseful"
STATUS_NOT_ACADEMIC = "notacademic"
STATUS_DUPLICATE = "duplicate"

REPORT_REFUSAL_CHOICES = (
    (None, "-"),
    (STATUS_UNCLEAR, "insufficiently clear"),
    (STATUS_INCORRECT, "not fully factually correct"),
    (STATUS_NOT_USEFUL, "not useful for the authors"),
    (STATUS_NOT_ACADEMIC, "not sufficiently academic in style"),
    (STATUS_DUPLICATE, "duplicate"),
)

REPORT_STATUSES = (
    (STATUS_DRAFT, "Draft"),
    (STATUS_VETTED, "Vetted"),
    (STATUS_UNVETTED, "Unvetted"),
    (STATUS_INCORRECT, "Rejected (incorrect)"),
    (STATUS_UNCLEAR, "Rejected (unclear)"),
    (STATUS_NOT_USEFUL, "Rejected (not useful)"),
    (STATUS_NOT_ACADEMIC, "Rejected (not academic in style)"),
    (STATUS_DUPLICATE, "Rejected (duplicate)"),
)

REPORT_NORMAL = "report_normal"
REPORT_POST_EDREC = "report_post_edrec"
REPORT_TYPES = (
    (REPORT_NORMAL, "Normal Report"),
    (REPORT_POST_EDREC, "Post-Editorial Recommendation Report"),
)

CYCLE_UNDETERMINED = ""
CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC = "default", "short", "direct_rec"
SUBMISSION_CYCLE_CHOICES = (
    (CYCLE_DEFAULT, "Default cycle"),
    (CYCLE_SHORT, "Short cycle"),
    (CYCLE_DIRECT_REC, "Direct editorial recommendation"),
)
SUBMISSION_CYCLES = (
    (CYCLE_UNDETERMINED, "Cycle undetermined"),
) + SUBMISSION_CYCLE_CHOICES

EVENT_GENERAL = "gen"
EVENT_FOR_EDADMIN = "edad"
EVENT_FOR_EIC = "eic"
EVENT_FOR_AUTHOR = "auth"
EVENT_TYPES = (
    (EVENT_GENERAL, "General comment"),
    (EVENT_FOR_EDADMIN, "Comment for EdAdmin"),
    (EVENT_FOR_EIC, "Comment for Editor-in-charge"),
    (EVENT_FOR_AUTHOR, "Comment for author"),
)


# Editorial recommendations
EIC_REC_PUBLISH = 1
EIC_REC_MINOR_REVISION = -1
EIC_REC_MAJOR_REVISION = -2
EIC_REC_REJECT = -3
EIC_REC_CHOICES = (
    (EIC_REC_PUBLISH, "Publish"),
    (EIC_REC_MINOR_REVISION, "Ask for minor revision"),
    (EIC_REC_MAJOR_REVISION, "Ask for major revision"),
    (EIC_REC_REJECT, "Reject"),
)
EIC_REC_CHOICES_SHORT = (
    (EIC_REC_PUBLISH, "Publish"),
    (EIC_REC_MINOR_REVISION, "Minor revision"),
    (EIC_REC_MAJOR_REVISION, "Major revision"),
    (EIC_REC_REJECT, "Reject"),
)


# Alternative recommendations
ALT_REC_RECONSULT_REFEREES = -4  # can be used as alternative to direct recommendation
ALT_REC_SEEK_ADDITIONAL_REFEREES = -5
ALT_REC_CHOICES = (
    (EIC_REC_PUBLISH, "Publish"),
    (ALT_REC_RECONSULT_REFEREES, "Reconsult previous referees"),
    (ALT_REC_SEEK_ADDITIONAL_REFEREES, "Seek additional referees"),
    (EIC_REC_MINOR_REVISION, "Ask for minor revision"),
    (EIC_REC_MAJOR_REVISION, "Ask for major revision"),
    (EIC_REC_REJECT, "Reject"),
)


# Tiering
TIER_I = 1
TIER_II = 2
TIER_III = 3
SUBMISSION_TIERS = (
    (
        TIER_I,
        "Tier I (surpasses expectations and criteria for this Journal; among top 10%)",
    ),
    (
        TIER_II,
        "Tier II (easily meets expectations and criteria for this Journal; among top 50%)",
    ),
    (TIER_III, "Tier III (meets expectations and criteria for this Journal)"),
)


VOTING_IN_PREP, PUT_TO_VOTING, VOTE_COMPLETED = (
    "voting_in_prep",
    "put_to_voting",
    "vote_completed",
)
DECISION_FIXED, DEPRECATED = "decision_fixed", "deprecated"
EIC_REC_STATUSES = (
    (VOTING_IN_PREP, "Voting in preparation"),
    (PUT_TO_VOTING, "Undergoing voting at the Editorial College"),
    (VOTE_COMPLETED, "Editorial College voting rounded up"),  # Seemlingly dead?
    (DECISION_FIXED, "Editorial Recommendation fixed"),
    (DEPRECATED, "Editorial Recommendation deprecated"),
)
EIC_REC_STATUSES_SHORT = (
    (VOTING_IN_PREP, "In preparation"),
    (PUT_TO_VOTING, "In voting"),
    (VOTE_COMPLETED, "Voting completed"),
    (DECISION_FIXED, "Rec. fixed"),
    (DEPRECATED, "Rec. deprecated"),
)


# Editorial decision
# (see other constants inside class; these are here because they use EIC_REC values)
EDITORIAL_DECISION_CHOICES = (
    (EIC_REC_PUBLISH, "Publish"),
    (EIC_REC_REJECT, "Reject"),
)


# Plagiarism Report statuses
STATUS_WAITING = "waiting"
STATUS_SENT, STATUS_RECEIVED = "sent", "received"
STATUS_FAILED_DOWNLOAD, STATUS_FAILED_UPLOAD = "fail_down", "fail_up"

PLAGIARISM_STATUSES = (
    (STATUS_WAITING, "Awaiting action"),
    (STATUS_SENT, "Sent succesfully, awaiting report"),
    (STATUS_RECEIVED, "Report received"),
    (STATUS_FAILED_DOWNLOAD, "Failed (downloading failed)"),
    (STATUS_FAILED_UPLOAD, "Failed (uploading failed)"),
)

# Preprint server-related constants
FIGSHARE_PREPRINT_SERVERS = ("ChemRxiv", "TechRxiv", "Advance")
