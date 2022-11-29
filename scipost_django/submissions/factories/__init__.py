__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .submission import (
    SubmissionFactory,
    SeekingAssignmentSubmissionFactory,
    InRefereeingSubmissionFactory,
    ResubmittedSubmissionFactory,
    ResubmissionFactory,
    PublishedSubmissionFactory,
)

from .assignment import EditorialAssignmentFactory

from .referee_invitation import (
    RefereeInvitationFactory,
    AcceptedRefereeInvitationFactory,
    FulfilledRefereeInvitationFactory,
    CancelledRefereeInvitationFactory,
)

from .report import (
    ReportFactory,
    DraftReportFactory,
    UnVettedReportFactory,
    VettedReportFactory,
)

from .recommendation import EICRecommendationFactory
