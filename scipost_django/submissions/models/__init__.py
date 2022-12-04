__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .submission import Submission, SubmissionEvent, SubmissionTiering

from .plagiarism_assessment import (
    PlagiarismAssessment,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)

from .iThenticate_report import iThenticateReport

from .assignment import EditorialAssignment

from .communication import EditorialCommunication

from .preprint_server import PreprintServer

from .referee_invitation import RefereeInvitation

from .report import Report

from .recommendation import EICRecommendation, AlternativeRecommendation

from .decision import EditorialDecision
