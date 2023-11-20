__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import *


class TestProfileFactory(TestCase):
    def test_can_create_profiles(self):
        profile = ProfileFactory()
        self.assertIsNotNone(profile)


class TestProfileNonDuplicatesFactory(TestCase):
    def test_can_create_profile_non_duplicates(self):
        profile_non_duplicate = ProfileNonDuplicatesFactory()
        self.assertIsNotNone(profile_non_duplicate)


class TestProfileEmailFactory(TestCase):
    def test_can_create_profile_emails(self):
        profile_email = ProfileEmailFactory()
        self.assertIsNotNone(profile_email)


class TestAffiliationFactory(TestCase):
    def test_can_create_affiliations(self):
        affiliation = AffiliationFactory()
        self.assertIsNotNone(affiliation)
