__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import BlogPostFactory, CategoryFactory


class TestCategoryFactory(TestCase):
    def test_can_create_categories(self):
        category = CategoryFactory()
        self.assertIsNotNone(category)


class TestBlogPostFactory(TestCase):
    def test_can_create_blog_posts(self):
        blog_post = BlogPostFactory()
        self.assertIsNotNone(blog_post)
