__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# All Submission statuses
STATUS_INCOMING = 'incoming'
STATUS_UNASSIGNED = 'unassigned'
STATUS_FAILED_PRESCREENING = 'failed_pre'
STATUS_EIC_ASSIGNED = 'assigned'
STATUS_ASSIGNMENT_FAILED = 'assignment_failed'
STATUS_RESUBMITTED = 'resubmitted'
STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE = 'puboffer_waiting'
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
    (STATUS_FAILED_PRESCREENING, 'Failed pre-screening'),
    (STATUS_EIC_ASSIGNED, 'Editor-in-charge assigned'),
    (STATUS_ASSIGNMENT_FAILED, 'Failed to assign Editor-in-charge; manuscript rejected'),
    (STATUS_RESUBMITTED, 'Has been resubmitted'),
    (STATUS_ACCEPTED, 'Publication decision taken: accept'),
    (STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE,
     'Accepted in other journal; awaiting puboffer acceptance'),
    (STATUS_REJECTED, 'Publication decision taken: reject'),
    (STATUS_WITHDRAWN, 'Withdrawn by the Authors'),
    (STATUS_PUBLISHED, 'Published'),
)

# Submissions which are currently under consideration
SUBMISSION_UNDER_CONSIDERATION = [
    STATUS_INCOMING, STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_RESUBMITTED,
    STATUS_ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE
]

# Submissions with these statuses never have required actions.
NO_REQUIRED_ACTION_STATUSES = [
    STATUS_UNASSIGNED,
    STATUS_FAILED_PRESCREENING,
    STATUS_ASSIGNMENT_FAILED,
    STATUS_REJECTED,
    STATUS_WITHDRAWN,
]

SUBMISSION_TYPE = (
    # ('', None),
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

STATUS_PREASSIGNED, STATUS_INVITED = 'preassigned', 'invited'
STATUS_DECLINED = 'declined'
STATUS_DEPRECATED, STATUS_COMPLETED = 'deprecated', 'completed'
STATUS_REPLACED = 'replaced'
ASSIGNMENT_STATUSES = (
    (STATUS_PREASSIGNED, 'Pre-assigned'),
    (STATUS_INVITED, 'Invited'),
    (STATUS_ACCEPTED, 'Accepted'),
    (STATUS_DECLINED, 'Declined'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_DEPRECATED, 'Deprecated'),
    (STATUS_REPLACED, 'Replaced'),
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
REPORT_ALT_JOURNAL = -4
REPORT_REC = (
    (None, '-'),
    (REPORT_PUBLISH_1, 'Publish (surpasses expectations and criteria for this Journal; among top 10%)'),
    (REPORT_PUBLISH_2, 'Publish (easily meets expectations and criteria for this Journal; among top 50%)'),
    (REPORT_PUBLISH_3, 'Publish (meets expectations and criteria for this Journal)'),
    (REPORT_MINOR_REV, 'Ask for minor revision'),
    (REPORT_MAJOR_REV, 'Ask for major revision'),
    (REPORT_ALT_JOURNAL, 'Accept in alternative Journal (see Report)'),
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


# Editorial recommendations
EIC_REC_PUBLISH = 1
EIC_REC_MINOR_REVISION = -1
EIC_REC_MAJOR_REVISION = -2
EIC_REC_REJECT = -3
EIC_REC_CHOICES = (
    (EIC_REC_PUBLISH, 'Publish'),
    (EIC_REC_MINOR_REVISION, 'Ask for minor revision'),
    (EIC_REC_MAJOR_REVISION, 'Ask for major revision'),
    (EIC_REC_REJECT, 'Reject'),
)


# Alternative recommendations
ALT_REC_RECONSULT_REFEREES = -4 # can be used as alternative to direct recommendation
ALT_REC_SEEK_ADDITIONAL_REFEREES = -5
ALT_REC_CHOICES = (
    (EIC_REC_PUBLISH, 'Publish'),
    (ALT_REC_RECONSULT_REFEREES, 'Reconsult previous referees'),
    (ALT_REC_SEEK_ADDITIONAL_REFEREES, 'Seek additional referees'),
    (EIC_REC_MINOR_REVISION, 'Ask for minor revision'),
    (EIC_REC_MAJOR_REVISION, 'Ask for major revision'),
    (EIC_REC_REJECT, 'Reject'),
)


# Tiering
TIER_I = 1
TIER_II = 2
TIER_III = 3
SUBMISSION_TIERS = (
    (TIER_I, 'Tier I (surpasses expectations and criteria for this Journal; among top 10%)'),
    (TIER_II, 'Tier II (easily meets expectations and criteria for this Journal; among top 50%)'),
    (TIER_III, 'Tier III (meets expectations and criteria for this Journal)'),
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


# Editorial decision
# (see other constants inside class; these are here because they use EIC_REC values)
EDITORIAL_DECISION_CHOICES = (
    (EIC_REC_PUBLISH, 'Publish'),
    (EIC_REC_REJECT, 'Reject'),
)


# Plagiarism Report statuses
STATUS_WAITING = 'waiting'
STATUS_SENT, STATUS_RECEIVED = 'sent', 'received'
STATUS_FAILED_DOWNLOAD, STATUS_FAILED_UPLOAD = 'fail_down', 'fail_up'

PLAGIARISM_STATUSES = (
    (STATUS_WAITING, 'Awaiting action'),
    (STATUS_SENT, 'Sent succesfully, awaiting report'),
    (STATUS_RECEIVED, 'Report received'),
    (STATUS_FAILED_DOWNLOAD, 'Failed (downloading failed)'),
    (STATUS_FAILED_UPLOAD, 'Failed (uploading failed)'),
)

# Define regexes
arxiv_regex_wo_vn = '[0-9]{4,}.[0-9]{4,}'
arxiv_regex_w_vn = '[0-9]{4,}.[0-9]{4,}v[0-9]{1,2}'
scipost_regex_wo_vn = 'scipost_[0-9]{4,}_[0-9]{4,}'
scipost_regex_w_vn = 'scipost_[0-9]{4,}_[0-9]{4,}v[0-9]{1,2}'
SUBMISSIONS_COMPLETE_REGEX = '(?P<identifier_w_vn_nr>(%s|%s))' % (arxiv_regex_w_vn, scipost_regex_w_vn)


# `EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS` tracks the regex rules for the manuscripts
# submitted per journal.
#
# CAUTION: *triple* check whether the `default` regex also meets any other explicit journal regex!
EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS = {
    'default': SUBMISSIONS_COMPLETE_REGEX
}
