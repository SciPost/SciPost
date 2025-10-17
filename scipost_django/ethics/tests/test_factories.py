__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import (
    ConflictofInterestFactory,
    ProfileRedFlagFactory,
    SubmissionClearanceFactory,
    SubmissionRedFlagFactory,
)


class TestConflictofInterestFactory(TestCase):
    def test_can_create_conflicts_of_interest(self):
        conflict_of_interest = ConflictofInterestFactory()

        self.assertIsNotNone(conflict_of_interest)

    def test_conflict_of_interest_declaration_by_either_party(self):
        conflict_of_interest = ConflictofInterestFactory()

        self.assertIn(
            conflict_of_interest.declared_by.profile,
            [conflict_of_interest.profile, conflict_of_interest.related_profile],
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
