from django.test import TestCase, tag

from common.helpers.test import add_groups_and_permissions
from scipost.models import Contributor

from .constants import STATUS_UNASSIGNED
from .factories import UnassignedSubmissionFactory


class TestDefaultSubmissionCycle(TestCase):
    '''
    This TestCase should act as a master test to check all steps in the
    submission's cycle: default.
    '''

    def setUp(self):
        add_groups_and_permissions()
        self.new_submission = UnassignedSubmissionFactory.build()

    @tag('cycle', 'core')
    def test_init_submission_factory_is_valid(self):
        """Ensure valid fields for the factory."""
        self.assertEqual(self.new_submission.status, STATUS_UNASSIGNED)
        self.assertIsNone(self.new_submission.editor_in_charge)
        self.assertTrue(self.new_submission.is_current)
        self.assertFalse(self.new_submission.is_resubmission)
        self.assertIsNot(self.new_submission.title, '')
        self.assertIsInstance(self.new_submission.submitted_by, Contributor)
        self.assertFalse(self.new_submission.open_for_commenting)
        self.assertFalse(self.new_submission.open_for_reporting)

    @tag('cycle', 'core')
    def test_initial_cycle_required_actions(self):
        """Test valid required actions for default cycle."""
        self.assertFalse(self.new_submission.cycle.get_required_actions())
