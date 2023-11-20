__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import *


class TestSeriesFactory(TestCase):
    def test_can_create_series(self):
        series = SeriesFactory()
        self.assertIsNotNone(series)


class TestCollectionFactory(TestCase):
    def test_can_create_collections(self):
        collection = CollectionFactory()
        self.assertIsNotNone(collection)
