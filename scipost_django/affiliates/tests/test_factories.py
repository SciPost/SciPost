__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import (
    AffiliateJournalFactory,
    AffiliateJournalYearSubsidyFactory,
    AffiliatePubFractionFactory,
    AffiliatePublicationFactory,
    AffiliatePublisherFactory,
)


class TestAffiliateJournalFactory(TestCase):
    def test_can_create_affiliate_journals(self):
        affiliate_journal = AffiliateJournalFactory()
        self.assertIsNotNone(affiliate_journal)


class TestAffiliatePublisherFactory(TestCase):
    def test_can_create_affiliate_publishers(self):
        affiliate_publisher = AffiliatePublisherFactory()
        self.assertIsNotNone(affiliate_publisher)


class TestAffiliatePubFractionFactory(TestCase):
    def test_can_create_pub_fractions(self):
        pub_fraction = AffiliatePubFractionFactory()
        self.assertIsNotNone(pub_fraction)


class TestAffiliatePublicationFactory(TestCase):
    def test_can_create_affiliate_publications(self):
        affiliate_publication = AffiliatePublicationFactory()
        self.assertIsNotNone(affiliate_publication)


class TestAffiliateJournalYearSubsidyFactory(TestCase):
    def test_can_create_affiliate_journal_year_subsidies(self):
        affiliate_journal_year_subsidy = AffiliateJournalYearSubsidyFactory()
        self.assertIsNotNone(affiliate_journal_year_subsidy)
