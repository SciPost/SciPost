STATUS_UNASSIGNED = 'unassigned'
STATUS_RESUBMISSION_INCOMING = 'resubmitted_incoming'
STATUS_REVISION_REQUESTED = 'revision_requested'
STATUS_EIC_ASSIGNED = 'EICassigned'
STATUS_AWAITING_ED_REC = 'awaiting_ed_rec'
STATUS_REVIEW_CLOSED = 'review_closed'
STATUS_ACCEPTED = 'accepted'
STATUS_PUBLISHED = 'published'
STATUS_REJECTED = 'rejected'
STATUS_REJECTED_VISIBLE = 'rejected_visible'
STATUS_RESUBMITTED = 'resubmitted'
STATUS_RESUBMITTED_REJECTED = 'resubmitted_and_rejected'
STATUS_RESUBMITTED_REJECTED_VISIBLE = 'resubmitted_and_rejected_visible'
SUBMISSION_STATUS = (
    (STATUS_UNASSIGNED, 'Unassigned, undergoing pre-screening'),
    (STATUS_RESUBMISSION_INCOMING, 'Resubmission incoming'),
    ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'),
    (STATUS_EIC_ASSIGNED, 'Editor-in-charge assigned, manuscript under review'),
    (STATUS_REVIEW_CLOSED, 'Review period closed, editorial recommendation pending'),
    # If revisions required: resubmission creates a new Submission object
    (STATUS_REVISION_REQUESTED, 'Editor-in-charge has requested revision'),
    (STATUS_RESUBMITTED, 'Has been resubmitted'),
    (STATUS_RESUBMITTED_REJECTED, 'Has been resubmitted and subsequently rejected'),
    (STATUS_RESUBMITTED_REJECTED_VISIBLE,
     'Has been resubmitted and subsequently rejected (still publicly visible)'),
    # If acceptance/rejection:
    ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'),
    ('put_to_EC_voting', 'Undergoing voting at the Editorial College'),
    (STATUS_AWAITING_ED_REC, 'Awaiting Editorial Recommendation'),
    ('EC_vote_completed', 'Editorial College voting rounded up'),
    (STATUS_ACCEPTED, 'Publication decision taken: accept'),
    (STATUS_REJECTED, 'Publication decision taken: reject'),
    (STATUS_REJECTED_VISIBLE, 'Publication decision taken: reject (still publicly visible)'),
    (STATUS_PUBLISHED, 'Published'),
    # If withdrawn:
    ('withdrawn', 'Withdrawn by the Authors'),
)

SUBMISSION_HTTP404_ON_EDITORIAL_PAGE = [
    'assignment_failed',
    STATUS_PUBLISHED,
    'withdrawn',
    STATUS_REJECTED,
    STATUS_REJECTED_VISIBLE,
]

SUBMISSION_STATUS_OUT_OF_POOL = SUBMISSION_HTTP404_ON_EDITORIAL_PAGE + [
    'resubmitted'
]

SUBMISSION_EXCLUDE_FROM_REPORTING = SUBMISSION_HTTP404_ON_EDITORIAL_PAGE + [
    STATUS_AWAITING_ED_REC,
    # STATUS_REVIEW_CLOSED,
    # STATUS_ACCEPTED,
    # 'voting_in_preparation',
    # 'put_to_EC_voting',
    # 'withdrawn',
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
    'assignment_failed',
    'resubmitted_rejected',
    STATUS_RESUBMITTED_REJECTED,
    'rejected',
    'withdrawn',
]

# Submissions which should not appear in search lists
SUBMISSION_STATUS_PUBLICLY_UNLISTED = SUBMISSION_STATUS_PUBLICLY_INVISIBLE + [
    'resubmitted',
    'resubmitted_rejected_visible',
    STATUS_RESUBMITTED_REJECTED_VISIBLE,
    'published'
]

# Submissions for which voting on a related recommendation is deprecated:
SUBMISSION_STATUS_VOTING_DEPRECATED = [
    'rejected',
    'published',
    'withdrawn',
]

SUBMISSION_TYPE = (
    ('Letter', 'Letter (broad-interest breakthrough results)'),
    ('Article', 'Article (in-depth reports on specialized research)'),
    ('Review', 'Review (candid snapshot of current research in a given area)'),
)

NO_REQUIRED_ACTION_STATUSES = SUBMISSION_STATUS_PUBLICLY_INVISIBLE + [
    STATUS_UNASSIGNED,
    STATUS_RESUBMISSION_INCOMING
]

ED_COMM_CHOICES = (
    ('EtoA', 'Editor-in-charge to Author'),
    ('EtoR', 'Editor-in-charge to Referee'),
    ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'),
    ('AtoE', 'Author to Editor-in-charge'),
    ('RtoE', 'Referee to Editor-in-Charge'),
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
    ('NIE', 'Not interested enough'),
    ('DNP', 'SciPost should not even consider this paper'),
)

REFEREE_QUALIFICATION = (
    (4, 'expert in this subject'),
    (3, 'very knowledgeable in this subject'),
    (2, 'knowledgeable in this subject'),
    (1, 'generally qualified'),
    (0, 'not qualified'),
)

QUALITY_SPEC = (
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
    (101, '-'),
    (100, 'top'),
    (80, 'high'),
    (60, 'good'),
    (40, 'ok'),
    (20, 'low'),
    (0, 'poor')
)

REPORT_REC = (
    (1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select) NOTE: SELECT NOT YET OPEN, STARTS EARLY 2017'),
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

CYCLE_DEFAULT = 'default'
CYCLE_SHORT = 'short'
CYCLE_DIRECT_REC = 'direct_rec'
SUBMISSION_CYCLES = (
    (CYCLE_DEFAULT, 'Default cycle'),
    (CYCLE_SHORT, 'Short cycle'),
    (CYCLE_DIRECT_REC, 'Direct editorial recommendation'),
)
