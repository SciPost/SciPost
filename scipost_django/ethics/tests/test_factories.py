__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import (
    CompetingInterestFactory,
    ProfileRedFlagFactory,
    SubmissionClearanceFactory,
    SubmissionRedFlagFactory,
)


class TestCompetingInterestFactory(TestCase):
    def test_can_create_competing_interests(self):
        competing_interest = CompetingInterestFactory()

        self.assertIsNotNone(competing_interest)

    def test_competing_interest_declaration_by_either_party(self):
        competing_interest = CompetingInterestFactory()

        self.assertIn(
            competing_interest.declared_by.profile,
            [competing_interest.profile, competing_interest.related_profile],
        )


class TestSubmissionClearanceFactory(TestCase):
    def test_can_create_submission_clearances(self):
        submission_clearance = SubmissionClearanceFactory()
        self.assertIsNotNone(submission_clearance)


class TestSubmissionRedFlagFactory(TestCase):
    def test_can_create_submission_red_flags(self):
        submission_red_flag = SubmissionRedFlagFactory()
        self.assertIsNotNone(submission_red_flag)


class TestProfileRedFlagFactory(TestCase):
    def test_can_create_profile_red_flags(self):
        profile_red_flag = ProfileRedFlagFactory()
        self.assertIsNotNone(profile_red_flag)
