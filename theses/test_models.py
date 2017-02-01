import re

from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import ThesisLink
from .factories import ThesisLinkFactory


class ThesisLinkTestCase(TestCase):
    fixtures = ['permissions', 'groups']

    def test_domain_cannot_be_blank(self):
        thesis_link = ThesisLinkFactory()
        thesis_link.domain = ""
        self.assertRaisesRegexp(ValidationError, re.compile(r'domain'),
                                thesis_link.full_clean)
