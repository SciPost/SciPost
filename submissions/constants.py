__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from journals.constants import SCIPOST_JOURNAL_PHYSICS


STATUS_UNASSIGNED = 'unassigned'
STATUS_ASSIGNMENT_FAILED = 'assignment_failed'
STATUS_RESUBMISSION_INCOMING = 'resubmitted_incoming'
STATUS_REVISION_REQUESTED = 'revision_requested'
STATUS_EIC_ASSIGNED = 'assigned'
STATUS_AWAITING_ED_REC = 'awaiting_ed_rec'
STATUS_REVIEW_CLOSED = 'review_closed'
STATUS_ACCEPTED = 'accepted'
STATUS_PUBLISHED = 'published'
STATUS_REJECTED = 'rejected'
STATUS_REJECTED_VISIBLE = 'rejected_visible'
STATUS_RESUBMITTED = 'resubmitted'
STATUS_RESUBMITTED_REJECTED = 'resubmitted_and_rejected'
STATUS_RESUBMITTED_REJECTED_VISIBLE = 'resubmitted_and_rejected_visible'
STATUS_VOTING_IN_PREPARATION = 'voting_in_preparation'
STATUS_PUT_TO_EC_VOTING = 'put_to_EC_voting'
STATUS_EC_VOTE_COMPLETED = 'EC_vote_completed'
STATUS_WITHDRAWN = 'withdrawn'

# New:
STATUS_NEW_INCOMING = 'unassigned_incoming'
STATUS_EIC_REC_FORMULATED = 'recommendation_formulated'

# All possible Submission statuses
SUBMISSION_STATUS = (
    (STATUS_NEW_INCOMING, 'Submission incoming, undergoing pre-screening'),
    (STATUS_UNASSIGNED, 'Unassigned, awaiting editor assignment'),
    (STATUS_EIC_ASSIGNED, 'Editor-in-charge assigned, manuscript under review'),
    (STATUS_ASSIGNMENT_FAILED, 'Failed to assign Editor-in-charge; manuscript rejected'),
    (STATUS_RESUBMITTED, 'Has been resubmitted'),
    (STATUS_ACCEPTED, 'Publication decision taken: accept'),
    (STATUS_REJECTED, 'Publication decision taken: reject'),
    (STATUS_WITHDRAWN, 'Withdrawn by the Authors'),
    (STATUS_PUBLISHED, 'Published'),
)


SUBMISSION_HTTP404_ON_EDITORIAL_PAGE = [
    STATUS_ASSIGNMENT_FAILED,
    STATUS_PUBLISHED,
    STATUS_WITHDRAWN,
    STATUS_REJECTED,
    STATUS_REJECTED_VISIBLE,
]

SUBMISSION_STATUS_OUT_OF_POOL = SUBMISSION_HTTP404_ON_EDITORIAL_PAGE + [
    STATUS_RESUBMITTED
]

SUBMISSION_EXCLUDE_FROM_REPORTING = SUBMISSION_HTTP404_ON_EDITORIAL_PAGE + [
    # STATUS_AWAITING_ED_REC,
    # STATUS_REVIEW_CLOSED,
    # STATUS_ACCEPTED,
    # STATUS_VOTING_IN_PREPARATION,
    # STATUS_PUT_TO_EC_VOTING,
    STATUS_WITHDRAWN,
]

# Submissions which are allowed/required to submit a EIC Recommendation
SUBMISSION_EIC_RECOMMENDATION_REQUIRED = [
    STATUS_EIC_ASSIGNED,
    STATUS_REVIEW_CLOSED,
    STATUS_AWAITING_ED_REC
]

# Submissions which should not be viewable (except by admins, Fellows and authors)
SUBMISSION_STATUS_PUBLICLY_INVISIBLE = [
    STATUS_UNASSIGNED,
    STATUS_RESUBMISSION_INCOMING,
    STATUS_ASSIGNMENT_FAILED,
    STATUS_RESUBMITTED_REJECTED,
    STATUS_REJECTED,
    STATUS_WITHDRAWN,
]

# Submissions which should not appear in search lists
SUBMISSION_STATUS_PUBLICLY_UNLISTED = SUBMISSION_STATUS_PUBLICLY_INVISIBLE + [
    STATUS_RESUBMITTED,
    STATUS_RESUBMITTED_REJECTED_VISIBLE,
    STATUS_PUBLISHED
]

# Submissions for which voting on a related recommendation is deprecated:
SUBMISSION_STATUS_VOTING_DEPRECATED = [
    STATUS_REJECTED,
    STATUS_PUBLISHED,
    STATUS_WITHDRAWN,
]

SUBMISSION_TYPE = (
    ('Letter', 'Letter (broad-interest breakthrough results)'),
    ('Article', 'Article (in-depth reports on specialized research)'),
    ('Review', 'Review (candid snapshot of current research in a given area)'),
)

NO_REQUIRED_ACTION_STATUSES = [
    STATUS_UNASSIGNED,
    STATUS_ASSIGNMENT_FAILED,
    STATUS_RESUBMITTED_REJECTED,
    STATUS_REJECTED,
    STATUS_WITHDRAWN,
]

ED_COMM_CHOICES = (
    ('EtoA', 'Editor-in-charge to Author'),
    ('EtoR', 'Editor-in-charge to Referee'),
    ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'),
    ('AtoE', 'Author to Editor-in-charge'),
    ('RtoE', 'Referee to Editor-in-charge'),
    ('StoE', 'SciPost Editorial Administration to Editor-in-charge'),
)

ASSIGNMENT_BOOL = ((True, 'Accept'), (False, 'Decline'))
ASSIGNMENT_NULLBOOL = ((None, 'Response pending'), (True, 'Accept'), (False, 'Decline'))

ASSIGNMENT_REFUSAL_REASONS = (
    ('BUS', 'Too busy'),
    ('VAC', 'Away on vacation'),
    ('COI', 'Conflict of interest: coauthor in last 5 years'),
    ('CCC', 'Conflict of interest: close colleague'),
    ('NIR', 'Cannot give an impartial assessment'),
    ('OFE', 'Outside of my field of expertise'),
    ('NIE', 'Not interested enough'),
    ('DNP', 'SciPost should not even consider this paper'),
)

REFEREE_QUALIFICATION = (
    (None, '-'),
    (4, 'expert in this subject'),
    (3, 'very knowledgeable in this subject'),
    (2, 'knowledgeable in this subject'),
    (1, 'generally qualified'),
    (0, 'not qualified'),
)

QUALITY_SPEC = (
    (None, '-'),
    (6, 'perfect'),
    (5, 'excellent'),
    (4, 'good'),
    (3, 'reasonable'),
    (2, 'acceptable'),
    (1, 'below threshold'),
    (0, 'mediocre'),
)

# Only values between 0 and 100 are kept, anything outside those limits is discarded.
RANKING_CHOICES = (
    (None, '-'),
    (100, 'top'),
    (80, 'high'),
    (60, 'good'),
    (40, 'ok'),
    (20, 'low'),
    (0, 'poor')
)

REPORT_REC = (
    (None, '-'),
    (1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select)'),
    (2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (3, 'Publish as Tier III (meets the criteria of this journal)'),
    (-1, 'Ask for minor revision'),
    (-2, 'Ask for major revision'),
    (-3, 'Reject')
)

#
# Reports
#
REPORT_ACTION_ACCEPT = 'accept'
REPORT_ACTION_REFUSE = 'refuse'
REPORT_ACTION_CHOICES = (
    (REPORT_ACTION_ACCEPT, 'accept'),
    (REPORT_ACTION_REFUSE, 'refuse'),
)

STATUS_DRAFT = 'draft'
STATUS_VETTED = 'vetted'
STATUS_UNVETTED = 'unvetted'
STATUS_UNCLEAR = 'unclear'
STATUS_INCORRECT = 'incorrect'
STATUS_NOT_USEFUL = 'notuseful'
STATUS_NOT_ACADEMIC = 'notacademic'

REPORT_REFUSAL_CHOICES = (
    (None, '-'),
    (STATUS_UNCLEAR, 'insufficiently clear'),
    (STATUS_INCORRECT, 'not fully factually correct'),
    (STATUS_NOT_USEFUL, 'not useful for the authors'),
    (STATUS_NOT_ACADEMIC, 'not sufficiently academic in style'),
)

REPORT_STATUSES = (
    (STATUS_DRAFT, 'Draft'),
    (STATUS_VETTED, 'Vetted'),
    (STATUS_UNVETTED, 'Unvetted'),
    (STATUS_INCORRECT, 'Rejected (incorrect)'),
    (STATUS_UNCLEAR, 'Rejected (unclear)'),
    (STATUS_NOT_USEFUL, 'Rejected (not useful)'),
    (STATUS_NOT_ACADEMIC, 'Rejected (not academic in style)')
)

REPORT_NORMAL = 'report_normal'
REPORT_POST_EDREC = 'report_post_edrec'
REPORT_TYPES = (
    (REPORT_NORMAL, 'Normal Report'),
    (REPORT_POST_EDREC, 'Post-Editorial Recommendation Report'),
)

POST_PUBLICATION_STATUSES = [
    STATUS_AWAITING_ED_REC,
    STATUS_REVIEW_CLOSED,
    STATUS_ACCEPTED,
    STATUS_VOTING_IN_PREPARATION,
    STATUS_PUT_TO_EC_VOTING,
]

CYCLE_DEFAULT = 'default'
CYCLE_SHORT = 'short'
CYCLE_DIRECT_REC = 'direct_rec'
SUBMISSION_CYCLES = (
    (CYCLE_DEFAULT, 'Default cycle'),
    (CYCLE_SHORT, 'Short cycle'),
    (CYCLE_DIRECT_REC, 'Direct editorial recommendation'),
)

EVENT_GENERAL = 'gen'
EVENT_FOR_EIC = 'eic'
EVENT_FOR_AUTHOR = 'auth'
EVENT_TYPES = (
    (EVENT_GENERAL, 'General comment'),
    (EVENT_FOR_EIC, 'Comment for Editor-in-charge'),
    (EVENT_FOR_AUTHOR, 'Comment for author'),
)

VOTING_IN_PREP, PUT_TO_VOTING, VOTE_COMPLETED = 'voting_in_prep', 'put_to_voting', 'vote_completed'
DECISION_FIXED, DEPRECATED = 'decision_fixed', 'deprecated'
EIC_REC_STATUSES = (
    (VOTING_IN_PREP, 'Voting in preparation'),
    (PUT_TO_VOTING, 'Undergoing voting at the Editorial College'),
    (VOTE_COMPLETED, 'Editorial College voting rounded up'),
    (DECISION_FIXED, 'Editorial Recommendation fixed'),
    (DEPRECATED, 'Editorial Recommendation deprecated'),
)

# Use `.format()` https://docs.python.org/3.5/library/string.html#format-string-syntax
# In your regex multiple brackets may occur;
# Please make sure to double them in that case as per instructions in the reference!
SUBMISSIONS_NO_VN_REGEX = '(?P<arxiv_identifier_wo_vn_nr>[0-9]{4,}.[0-9]{4,})'
SUBMISSIONS_COMPLETE_REGEX = '(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{4,}v[0-9]{1,2})'


# `EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS` tracks the regex rules for the manuscripts
# submitted per journal.
#
# CAUTION: *triple* check whether the `default` regex also meets any other explicit journal regex!
EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS = {
    SCIPOST_JOURNAL_PHYSICS: '(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{4,}v[0-9]{1,2})',
    'default': SUBMISSIONS_COMPLETE_REGEX
}
