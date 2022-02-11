__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase

from ..models import Profile
from ..factories import ProfileFactory

from common.helpers.test import add_groups_and_permissions


class ProfileTestCase(TestCase):
    def setUp(self):
        add_groups_and_permissions()

    def test_last_name_cannot_be_blank(self):
        profile = ProfileFactory()
        self.assertTrue(profile.last_name is not None)
