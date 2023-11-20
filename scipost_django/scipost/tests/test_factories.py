from django.test import TestCase

from profiles.factories import ProfileFactory
from scipost.constants import AUTHORSHIP_CLAIM_ACCEPTED

from ..factories import *

from submissions.factories import SubmissionFactory
from journals.factories import JournalPublicationFactory


class TestContributorFactory(TestCase):
    def test_can_create_contributors(self):
        contributor = ContributorFactory()

        self.assertIsNotNone(contributor)

    def test_contributor_user_and_profile_have_same_name(self):
        contributor = ContributorFactory()

        self.assertEqual(contributor.profile.first_name, contributor.user.first_name)
        self.assertEqual(contributor.profile.last_name, contributor.user.last_name)

    def test_contributor_user_name_propagates_to_profile(self):
        contributor = ContributorFactory(user__first_name="John", user__last_name="Doe")

        self.assertEqual(contributor.profile.first_name, "John")
        self.assertEqual(contributor.profile.last_name, "Doe")

    def test_contributor_from_user_refers_to_user_used(self):
        user = UserFactory(first_name="John", last_name="Doe")
        contributor = ContributorFactory(user=user)

        self.assertEqual(contributor.user, user)

    def test_contributor_from_profile_refers_to_profile_used(self):
        profile = ProfileFactory(title="Mr", first_name="John", last_name="Doe")
        contributor = ContributorFactory.from_profile(profile)

        self.assertEqual(contributor.profile, profile)


class TestUserFactory(TestCase):
    def test_can_create_users(self):
        user = UserFactory()
        self.assertIsNotNone(user)

    def test_user_username_contains_first_and_last_name(self):
        user = UserFactory(first_name="John", last_name="Doe")
        self.assertEqual(user.username, "jdoe")


class TestTOTPDeviceFactory(TestCase):
    def test_can_create_totp_devices(self):
        totp_device = TOTPDeviceFactory()
        self.assertIsNotNone(totp_device)


class TestSubmissionRemarkFactory(TestCase):
    def test_can_create_submission_remarks(self):
        submission_remark = SubmissionRemarkFactory()
        self.assertIsNotNone(submission_remark)


class TestUnavailabilityPeriodFactory(TestCase):
    def test_can_create_unavailability_periods(self):
        unavailability_period = UnavailabilityPeriodFactory()
        self.assertIsNotNone(unavailability_period)


class TestAuthorshipClaimFactory(TestCase):
    def test_can_create_authorship_claims(self):
        authorship_claim = AuthorshipClaimFactory()
        self.assertIsNotNone(authorship_claim)

    def test_non_pending_authorship_claim_has_editor(self):
        authorship_claim = AuthorshipClaimFactory(status=AUTHORSHIP_CLAIM_ACCEPTED)
        self.assertIsNotNone(authorship_claim.vetted_by)
        self.assertIsNotNone(authorship_claim)

    def test_pending_authorship_claim_has_no_editor(self):
        authorship_claim = AuthorshipClaimFactory(status=AUTHORSHIP_CLAIM_PENDING)
        self.assertIsNone(authorship_claim.vetted_by)
        self.assertIsNotNone(authorship_claim)


class TestCitationNotificationFactory(TestCase):
    def test_can_create_citation_notifications_with_publication(self):
        citation_notification = CitationNotificationFactory(
            item=JournalPublicationFactory()
        )
        self.assertIsNotNone(citation_notification.cited_in_publication)
        self.assertIsNone(citation_notification.cited_in_submission)
        self.assertIsNotNone(citation_notification)

    def test_can_create_citation_notifications_with_submission(self):
        citation_notification = CitationNotificationFactory(item=SubmissionFactory())
        self.assertIsNotNone(citation_notification.cited_in_submission)
        self.assertIsNone(citation_notification.cited_in_publication)
        self.assertIsNotNone(citation_notification)
