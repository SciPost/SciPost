__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from proceedings.factories import ProceedingsFactory


class TestProceedingsFactory(TestCase):
    def test_can_create_proceedingss(self):
        proceedings = ProceedingsFactory()
        self.assertIsNotNone(proceedings)
