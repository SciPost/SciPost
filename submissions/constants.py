STATUS_UNASSIGNED = 'unassigned'
STATUS_RESUBMISSION_SCREENING = 'resubmitted_incomin'
STATUS_REVISION_REQUESTED = 'revision_requested'
SUBMISSION_STATUS = (
    (STATUS_UNASSIGNED, 'Unassigned, undergoing pre-screening'),
    (STATUS_RESUBMISSION_SCREENING, 'Resubmission incoming, undergoing pre-screening'),
    ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'),
    ('EICassigned', 'Editor-in-charge assigned, manuscript under review'),
    ('review_closed', 'Review period closed, editorial recommendation pending'),
    # If revisions required: resubmission creates a new Submission object
    (STATUS_REVISION_REQUESTED, 'Editor-in-charge has requested revision'),
    ('resubmitted', 'Has been resubmitted'),
    ('resubmitted_and_rejected', 'Has been resubmitted and subsequently rejected'),
    ('resubmitted_and_rejected_visible',
     'Has been resubmitted and subsequently rejected (still publicly visible)'),
    # If acceptance/rejection:
    ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'),
    ('put_to_EC_voting', 'Undergoing voting at the Editorial College'),
    ('EC_vote_completed', 'Editorial College voting rounded up'),
    ('accepted', 'Publication decision taken: accept'),
    ('rejected', 'Publication decision taken: reject'),
    ('rejected_visible', 'Publication decision taken: reject (still publicly visible)'),
    ('published', 'Published'),
    # If withdrawn:
    ('withdrawn', 'Withdrawn by the Authors'),
)

SUBMISSION_STATUS_OUT_OF_POOL = [
    'assignment_failed',
    'resubmitted',
    'published',
    'withdrawn',
    'rejected',
    'rejected_visible',
]

# Submissions which should not be viewable (except by admins, Fellows and authors)
SUBMISSION_STATUS_PUBLICLY_INVISIBLE = [
    STATUS_UNASSIGNED,
    STATUS_RESUBMISSION_SCREENING,
    'assignment_failed',
    'resubmitted_rejected',
    'rejected',
    'withdrawn',
]

# Submissions which should not appear in search lists
SUBMISSION_STATUS_PUBLICLY_UNLISTED = SUBMISSION_STATUS_PUBLICLY_INVISIBLE + [
    'resubmitted',
    'resubmitted_rejected_visible',
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
REPORT_ACTION_ACCEPT = 1
REPORT_ACTION_REFUSE = 2
REPORT_ACTION_CHOICES = (
    (REPORT_ACTION_ACCEPT, 'accept'),
    (REPORT_ACTION_REFUSE, 'refuse'),
)

STATUS_VETTED = 1
STATUS_UNVETTED = 0
STATUS_UNCLEAR = -1
STATUS_INCORRECT = -2
STATUS_NOT_USEFUL = -3
STATUS_NOT_ACADEMIC = -4

REPORT_REFUSAL_NONE = 0
REPORT_REFUSAL_CHOICES = (
    (STATUS_UNVETTED, '-'),
    (STATUS_UNCLEAR, 'insufficiently clear'),
    (STATUS_INCORRECT, 'not fully factually correct'),
    (STATUS_NOT_USEFUL, 'not useful for the authors'),
    (STATUS_NOT_ACADEMIC, 'not sufficiently academic in style'),
)

REPORT_STATUSES = (
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
