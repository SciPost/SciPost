__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase

from common.helpers.test import add_groups_and_permissions

from scipost.factories import ContributorFactory
from .factories import UnvettedCommentaryFactory


class TestCommentary(TestCase):
    def setUp(self):
        add_groups_and_permissions()
