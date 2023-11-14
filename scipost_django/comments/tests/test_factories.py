__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import ReplyCommentFactory, SubmissionCommentFactory


class TestReplyCommentFactory(TestCase):
    def test_can_create_reply_comments(self):
        reply_comment = ReplyCommentFactory()

        self.assertIsNotNone(reply_comment)


class TestSubmissionCommentFactory(TestCase):
    def test_can_create_submission_comments(self):
        submission_comment = SubmissionCommentFactory()

        self.assertIsNotNone(submission_comment)
