__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django.test import TestCase
from django.core.exceptions import ValidationError

from ..models import ThesisLink
from ..factories import ThesisLinkFactory
from common.helpers.test import add_groups_and_permissions


class ThesisLinkTestCase(TestCase):
    def setUp(self):
        add_groups_and_permissions()
