__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import *


class TestThesisLinkFactory(TestCase):
    def test_can_create_thesis_links(self):
        thesis_link = ThesisLinkFactory()
        self.assertIsNotNone(thesis_link)
