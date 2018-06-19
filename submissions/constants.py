__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from journals.constants import SCIPOST_JOURNAL_PHYSICS


# All Submission statuses
STATUS_INCOMING = 'incoming'
STATUS_UNASSIGNED = 'unassigned'
STATUS_EIC_ASSIGNED = 'assigned'
STATUS_ASSIGNMENT_FAILED = 'assignment_failed'
STATUS_RESUBMITTED = 'resubmitted'
STATUS_ACCEPTED = 'accepted'
STATUS_REJECTED = 'rejected'
STATUS_WITHDRAWN = 'withdrawn'
STATUS_PUBLISHED = 'published'

# Deprecated statuses
# TODO: Make sure cycles are chosen for this status:
# STATUS_RESUBMISSION_INCOMING = 'resubmitted_incoming'


# All possible Submission statuses
SUBMISSION_STATUS = (
    (STATUS_INCOMING, 'Submission incoming, undergoing pre-screening'),
    (STATUS_UNASSIGNED, 'Unassigned, awaiting editor assignment'),
    (STATUS_EIC_ASSIGNED, 'Editor-in-charge assigned'),
    (STATUS_ASSIGNMENT_FAILED, 'Failed to assign Editor-in-charge; manuscript rejected'),
    (STATUS_RESUBMITTED, 'Has been resubmitted'),
    (STATUS_ACCEPTED, 'Publication decision taken: accept'),
    (STATUS_REJECTED, 'Publication decision taken: reject'),
    (STATUS_WITHDRAWN, 'Withdrawn by the Authors'),
    (STATUS_PUBLISHED, 'Published'),
)

# Submissions with these statuses never have required actions.
NO_REQUIRED_ACTION_STATUSES = [
    STATUS_UNASSIGNED,
    STATUS_ASSIGNMENT_FAILED,
    STATUS_REJECTED,
    STATUS_WITHDRAWN,
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

REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3 = 1, 2, 3
REPORT_MINOR_REV, REPORT_MAJOR_REV = -1, -2
REPORT_REJECT = -3
REPORT_REC = (
    (None, '-'),
    (REPORT_PUBLISH_1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select)'),
    (REPORT_PUBLISH_2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (REPORT_PUBLISH_3, 'Publish as Tier III (meets the criteria of this journal)'),
    (REPORT_MINOR_REV, 'Ask for minor revision'),
    (REPORT_MAJOR_REV, 'Ask for major revision'),
    (REPORT_REJECT, 'Reject')
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

CYCLE_UNDETERMINED = ''
CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC = 'default', 'short', 'direct_rec'
SUBMISSION_CYCLE_CHOICES = (
    (CYCLE_DEFAULT, 'Default cycle'),
    (CYCLE_SHORT, 'Short cycle'),
    (CYCLE_DIRECT_REC, 'Direct editorial recommendation'),
)
SUBMISSION_CYCLES = ((CYCLE_UNDETERMINED, 'Cycle undetermined'),) + SUBMISSION_CYCLE_CHOICES

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
    (VOTE_COMPLETED, 'Editorial College voting rounded up'),  # Seemlingly dead?
    (DECISION_FIXED, 'Editorial Recommendation fixed'),
    (DEPRECATED, 'Editorial Recommendation deprecated'),
)

# Define regexes
arxiv_regex_wo_vn = '[0-9]{4,}.[0-9]{4,}'
arxiv_regex_w_vn = '[0-9]{4,}.[0-9]{4,}v[0-9]{1,2}'
scipost_regex_wo_vn = 'scipost_[0-9]{4,}.[0-9]{4,}'
scipost_regex_w_vn = 'scipost_[0-9]{4,}.[0-9]{4,}v[0-9]{1,2}'
SUBMISSIONS_NO_VN_REGEX = '(?P<identifier_wo_vn_nr>(%s|%s))' % (arxiv_regex_wo_vn, scipost_regex_wo_vn)
SUBMISSIONS_COMPLETE_REGEX = '(?P<identifier_w_vn_nr>(%s|%s))' % (arxiv_regex_w_vn, scipost_regex_w_vn)
SCIPOST_PREPRINT_W_VN_REGEX = '(?P<identifier_w_vn_nr>%s)' % scipost_regex_w_vn


# `EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS` tracks the regex rules for the manuscripts
# submitted per journal.
#
# CAUTION: *triple* check whether the `default` regex also meets any other explicit journal regex!
EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS = {
    # SCIPOST_JOURNAL_PHYSICS: '(?P<identifier_w_vn_nr>[0-9]{4,}.[0-9]{4,}v[0-9]{1,2})',
    'default': SUBMISSIONS_COMPLETE_REGEX
}
