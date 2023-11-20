__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from production.factories import (
    ProductionEventFactory,
    ProductionStreamFactory,
    ProductionUserFactory,
    ProofsFactory,
    ProofsRepositoryFactory,
)


class TestProductionUserFactory(TestCase):
    def test_can_create_production_users(self):
        production_user = ProductionUserFactory()
        self.assertIsNotNone(production_user)


class TestProductionStreamFactory(TestCase):
    def test_can_create_production_streams(self):
        production_stream = ProductionStreamFactory()
        self.assertIsNotNone(production_stream)


class TestProductionEventFactory(TestCase):
    def test_can_create_production_events(self):
        production_event = ProductionEventFactory()
        self.assertIsNotNone(production_event)


class TestProofsRepositoryFactory(TestCase):
    def test_can_create_proofs_repositoriess(self):
        proofs_repository = ProofsRepositoryFactory()
        self.assertIsNotNone(proofs_repository)


class TestProofsFactory(TestCase):
    def test_can_create_proofss(self):
        proofs = ProofsFactory()
        self.assertIsNotNone(proofs)
