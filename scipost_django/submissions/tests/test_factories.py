__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase


from ..factories import *


# Assignment
class TestEditorialAssignmentFactory(TestCase):
    def test_can_create_editorial_assignments(self):
        editorial_assignment = EditorialAssignmentFactory()
        self.assertIsNotNone(editorial_assignment)


# Communication
class TestEditorialCommunication(TestCase):
    def test_can_create_editorial_communications(self):
        editorial_communication = EditorialCommunicationFactory()
        self.assertIsNotNone(editorial_communication)


# Recommendation
class TestEICRecommendationFactory(TestCase):
    def test_can_create_eic_recommendations(self):
        eic_recommendation = EICRecommendationFactory()
        self.assertIsNotNone(eic_recommendation)


# Submissions
class TestSubmissionFactory(TestCase):
    def test_can_create_submissions(self):
        submission = SubmissionFactory()
        self.assertIsNotNone(submission)


class TestSubmissionAuthorProfileFactory(TestCase):
    def test_can_create_submission_author_profiles(self):
        submission_author_profile = SubmissionAuthorProfileFactory()
        self.assertIsNotNone(submission_author_profile)


class TestSubmissionEventFactory(TestCase):
    def test_can_create_submission_events(self):
        submission_event = SubmissionEventFactory()
        self.assertIsNotNone(submission_event)


class TestSubmissionTieringFactory(TestCase):
    def test_can_create_submission_tierings(self):
        submission_tiering = SubmissionTieringFactory()
        self.assertIsNotNone(submission_tiering)


# Reports
class TestReportFactory(TestCase):
    def test_can_create_reports(self):
        report = ReportFactory()
        self.assertIsNotNone(report)


# Referee Invitation
class TestRefereeInvitationFactory(TestCase):
    def test_can_create_unregistered_referee_invitations(self):
        referee_invitation = RefereeInvitationFactory()
        self.assertIsNone(referee_invitation.referee)
        self.assertIsNotNone(referee_invitation)

    def test_can_create_registered_referee_invitations(self):
        referee_invitation = RefereeInvitationFactory(registered=True)
        self.assertIsNotNone(referee_invitation)


# Readiness
class TestReadinessFactory(TestCase):
    def test_can_create_readinesses(self):
        readiness = ReadinessFactory()
        self.assertIsNotNone(readiness)


# Qualification
class TestQualificationFactory(TestCase):
    def test_can_create_qualifications(self):
        qualification = QualificationFactory()
        self.assertIsNotNone(qualification)


# Decision
class TestEditorialDecisionFactory(TestCase):
    def test_can_create_editorial_decisions(self):
        editorial_decision = EditorialDecisionFactory()
        self.assertIsNotNone(editorial_decision)


# Plagiarism Assessment
class TestInternalPlagiarismAssessmentFactory(TestCase):
    def test_can_create_internal_plagiarism_assessments(self):
        internal_plagiarism_assessment = InternalPlagiarismAssessmentFactory()
        self.assertIsNotNone(internal_plagiarism_assessment)


class TestiThenticatePlagiarismAssessmentFactory(TestCase):
    def test_can_create_ithenticate_plagiarism_assessments(self):
        ithenticate_plagiarism_assessment = iThenticatePlagiarismAssessmentFactory()
        self.assertIsNotNone(ithenticate_plagiarism_assessment)


# iThenticate Report
class TestiThenticateReportFactory(TestCase):
    def test_can_create_ithenticate_reports(self):
        ithenticate_report = iThenticateReportFactory()
        self.assertIsNotNone(ithenticate_report)


# Conditional Assignment Offer
class TestConditionalAssignmentOfferFactory(TestCase):
    def test_can_create_offers(self):
        offer = ConditionalAssignmentOfferFactory()
        self.assertIsNotNone(offer)


class TestJournalTransferOfferFactory(TestCase):
    def test_can_create_offers(self):
        offer = JournalTransferOfferFactory()
        self.assertIsNotNone(offer)
