__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .assignment import EditorialAssignmentQuerySet

from .communication import EditorialCommunicationQuerySet

from .decision import EditorialDecisionQuerySet

from .qualification import QualificationQuerySet

from .recommendation import EICRecommendationQuerySet

from .referee_invitation import RefereeInvitationQuerySet

from .report import ReportQuerySet

from .submission import SubmissionQuerySet, SubmissionEventQuerySet
