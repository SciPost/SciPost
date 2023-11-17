__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase
from ..factories import NewsItemFactory, NewsLetterFactory


class TestNewsLetterFactory(TestCase):
    def test_can_create_news_letters(self):
        news_letter = NewsLetterFactory()
        self.assertIsNotNone(news_letter)


class TestNewsItemFactory(TestCase):
    def test_can_create_news_items(self):
        news_item = NewsItemFactory()
        self.assertIsNotNone(news_item)
