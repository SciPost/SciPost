__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from commentaries.factories import CommentaryFactory


class TestCommentaryFactory(TestCase):
    def test_can_create_commentaries(self):
        commentary = CommentaryFactory()
        self.assertIsNotNone(commentary)
