__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.test import TestCase, tag

from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory
from scipost.models import Contributor

from ..constants import (
    CYCLE_DEFAULT,
    CYCLE_DIRECT_REC,
)
from ..exceptions import CycleUpdateDeadlineError
from ..factories import SeekingAssignmentSubmissionFactory, ResubmissionFactory

# from .utils import GeneralSubmissionCycle


# NOTED AS BROKEN 2019-11-08
# class TestDefaultSubmissionCycle(TestCase):
#     """Test all steps in the Submission default cycle."""

#     def setUp(self):
#         """Set up basics for all tests."""
#         self.submission_date = datetime.date.today()
#         add_groups_and_permissions()
#         ContributorFactory.create_batch(5)
#         self.new_submission = SeekingAssignmentSubmissionFactory(
#             dates__submission=self.submission_date
#         )

#     @tag('cycle', 'core')
#     def test_init_submission_factory_is_valid(self):
#         """Ensure valid fields for the factory."""
#         self.assertEqual(self.new_submission.status, self.new_submission.INCOMING)
#         self.assertIsNone(self.new_submission.editor_in_charge)
#         self.assertTrue(self.new_submission.is_latest)
#         self.assertFalse(self.new_submission.is_resubmission)
#         self.assertIsNot(self.new_submission.title, '')
#         self.assertIsInstance(self.new_submission.submitted_by, Contributor)
#         self.assertFalse(self.new_submission.open_for_commenting)
#         self.assertFalse(self.new_submission.open_for_reporting)
#         self.assertEqual(self.new_submission.submission_date, self.submission_date)

# NOTED AS BROKEN 2019-11-08
# ImportError: cannot import name 'GeneralSubmissionCycle'
# @tag('cycle', 'core')
# def test_initial_cycle_required_actions_and_deadline(self):
#     """Test valid required actions for default cycle."""
#     self.assertIsInstance(self.new_submission.cycle, GeneralSubmissionCycle)

#     # Explicit: No actions required if no EIC is assigned yet
#     self.assertFalse(self.new_submission.cycle.get_required_actions())

#     # Two weeks deadline check
#     self.new_submission.cycle.update_deadline()
#     real_report_deadline = self.submission_date + datetime.timedelta(days=28)
#     self.assertEqual(self.new_submission.reporting_deadline.day, real_report_deadline.day)
#     self.assertEqual(self.new_submission.reporting_deadline.month, real_report_deadline.month)
#     self.assertEqual(self.new_submission.reporting_deadline.year, real_report_deadline.year)
#     self.assertIsInstance(self.new_submission.reporting_deadline, datetime.datetime)


# NOTED AS BROKEN 2019-11-08
# class TestResubmissionSubmissionCycle(TestCase):
#     '''
#     This TestCase should act as a master test to check all steps in the
#     submission's cycle: resubmission.
#     '''

#     def setUp(self):
#         """Basics for all tests"""
#         self.submission_date = datetime.date.today()
#         add_groups_and_permissions()
#         ContributorFactory.create_batch(5)
#         self.submission = ResubmissionFactory(
#             dates__submission=self.submission_date
#         )

#     @tag('cycle', 'core')
#     def test_init_resubmission_factory_is_valid(self):
#         """Ensure valid fields for the factory."""
#         self.assertEqual(self.submission.status, self.submission.INCOMING)
#         self.assertIsInstance(self.submission.editor_in_charge, Contributor)
#         self.assertTrue(self.submission.is_latest)
#         self.assertTrue(self.submission.is_resubmission)
#         self.assertIsNot(self.submission.title, '')
#         self.assertIsInstance(self.submission.submitted_by, Contributor)
#         self.assertTrue(self.submission.open_for_commenting)
#         self.assertTrue(self.submission.open_for_reporting)
#         self.assertEqual(self.submission.submission_date, self.submission_date)
#         self.assertEqual(self.submission.refereeing_cycle, CYCLE_DEFAULT)

#     @tag('cycle', 'core')
#     def test_initial_cycle_required_actions_and_deadline(self):
#         """Test valid required actions for default cycle."""
#         self.assertRaises(CycleUpdateDeadlineError, self.submission.cycle.update_deadline)

#         # Update status for default cycle to check new status
#         self.submission.cycle.update_status()
#         self.assertEqual(self.submission.status, self.submission.REFEREEING_IN_PREPARATION)


# NOTED AS BROKEN 2019-11-08
# class TestResubmissionDirectSubmissionCycle(TestCase):
#     '''
#     This TestCase should act as a master test to check all steps in the
#     submission's cycle: resubmission (cycle: DIRECT_RECOMMENDATION).
#     '''

#     def setUp(self):
#         """Basics for all tests"""
#         self.submission_date = datetime.date.today()
#         add_groups_and_permissions()
#         ContributorFactory.create_batch(5)
#         self.submission = ResubmissionFactory(
#             dates__submission=self.submission_date,
#             refereeing_cycle=CYCLE_DIRECT_REC
#         )

#     @tag('cycle', 'core')
#     def test_init_resubmission_factory_is_valid(self):
#         """Ensure valid fields for the factory."""
#         self.assertEqual(self.submission.status, self.submission.INCOMING)
#         self.assertIsInstance(self.submission.editor_in_charge, Contributor)
#         self.assertTrue(self.submission.is_latest)
#         self.assertTrue(self.submission.is_resubmission)
#         self.assertIsNot(self.submission.title, '')
#         self.assertIsInstance(self.submission.submitted_by, Contributor)
#         self.assertTrue(self.submission.open_for_commenting)
#         self.assertTrue(self.submission.open_for_reporting)
#         self.assertEqual(self.submission.submission_date, self.submission_date)
#         self.assertEqual(self.submission.refereeing_cycle, CYCLE_DIRECT_REC)

#     @tag('cycle', 'core')
#     def test_initial_cycle_required_actions_and_deadline(self):
#         """Test valid required actions for default cycle."""
#         self.assertRaises(CycleUpdateDeadlineError, self.submission.cycle.update_deadline)

#         # Update status for default cycle to check new status
#         self.submission.cycle.update_status()
#         self.assertEqual(self.submission.status, self.submission.REFEREEING_IN_PREPARATION)
