__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import *


class TestQueueFactory(TestCase):
    def test_can_create_queues(self):
        queue = QueueFactory()
        self.assertIsNotNone(queue)


class TestTicketFactory(TestCase):
    def test_can_create_tickets(self):
        ticket = TicketFactory()
        self.assertIsNotNone(ticket)
