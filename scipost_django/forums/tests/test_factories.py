from django.test import TestCase
from ..factories import (
    ForumFactory,
    MeetingFactory,
    MotionFactory,
    PostFactory,
    ReplyPostFactory,
)


class TestForumFactory(TestCase):
    def test_can_create_forums(self):
        forum = ForumFactory()
        self.assertIsNotNone(forum)


class TestPostFactory(TestCase):
    def test_can_create_posts(self):
        post = PostFactory()
        self.assertIsNotNone(post)


class TestReplyPostFactory(TestCase):
    def test_can_create_reply_posts(self):
        parent_post = PostFactory()
        post = ReplyPostFactory(parent=parent_post)
        self.assertIsNotNone(post)
        self.assertEqual(post.parent, parent_post)


class TestMotionFactory(TestCase):
    def test_can_create_motions(self):
        motion = MotionFactory()
        self.assertIsNotNone(motion)


class TestMeetingFactory(TestCase):
    def test_can_create_meetings(self):
        meeting = MeetingFactory()
        self.assertIsNotNone(meeting)
