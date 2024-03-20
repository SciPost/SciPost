__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase
from ..factories import *


# Create your tests here.
class TestFunderFactory(TestCase):
    def test_can_create_funders(self):
        funder = FunderFactory()
        self.assertIsNotNone(funder)


class TestGrantFactory(TestCase):
    def test_can_create_grants(self):
        grant = GrantFactory()
        self.assertIsNotNone(grant)
