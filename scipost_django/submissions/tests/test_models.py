__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from common.faker import fake
from django.test import TestCase

from journals.models.journal import Journal
from submissions.factories.assignment import (
    ConditionalAssignmentOfferFactory,
    JournalTransferOfferFactory,
)
from submissions.factories.submission import SubmissionFactory
from submissions.models.assignment import ConditionalAssignmentOffer


class TestJournalTransferOfferAcceptance(TestCase):
    def test_accepting_offer_changes_journal(self) -> None:
        offer = JournalTransferOfferFactory(
            offered_until=fake.aware.date_time_this_month(
                after_now=True, before_now=False
            )
        )
        offer.accept(offer.submission.submitted_by)

        # Check the conditions have been applied
        alternative_journal = Journal.objects.get(
            id=offer.condition_details["alternative_journal_id"]
        )
        self.assertEqual(offer.submission.submitted_to, alternative_journal)


class TestConditionalAssignmentOfferAcceptance(TestCase):
    def setUp(self) -> None:
        self.submission = SubmissionFactory()
        self.offer = ConditionalAssignmentOfferFactory(
            submission=self.submission,
            offered_until=fake.aware.date_time_this_year(
                before_now=False, after_now=True
            ),
            condition_details={
                "alternative_journal_id": self.submission.submitted_to.id
            },  # Hack temporary fix
        )

    def test_can_accept_offer(self) -> None:
        self.offer.accept(self.offer.submission.submitted_by)

        self.assertEqual(self.offer.status, ConditionalAssignmentOffer.STATUS_ACCEPTED)
        self.assertIsNotNone(self.offer.accepted_on)
        self.assertIsNotNone(self.offer.accepted_by)

    def test_finalizing_offer(self):
        other_offers = ConditionalAssignmentOfferFactory.create_batch(
            5, submission=self.submission
        )

        self.offer.accept(self.offer.submission.submitted_by)
        self.offer.finalize()

        # Creates an editorial assignment for the self.offering fellow
        self.assertIsNotNone(
            self.offer.submission.editorial_assignments.filter(to=self.offer.offered_by)
        )
        self.assertEqual(self.offer.submission.editor_in_charge, self.offer.offered_by)
        self.assertEqual(self.offer.status, ConditionalAssignmentOffer.STATUS_FULFILLED)

        # Implicitly declines all other offers
        for other_offer in other_offers:
            other_offer.refresh_from_db()
            self.assertEqual(
                other_offer.status,
                ConditionalAssignmentOffer.STATUS_DECLINED,
            )


class TestConditionalAssignmentOfferAcceptanceFailure(TestCase):
    def setUp(self) -> None:
        self.submission = SubmissionFactory()

    def test_cannot_accept_expired_offer(self):
        with self.assertRaises(ValueError):
            offer = ConditionalAssignmentOfferFactory(
                offered_until=fake.aware.date_time_this_year(
                    before_now=True, after_now=False
                ),
                condition_details={
                    "alternative_journal_id": self.submission.submitted_to.id
                },  # Hack temporary fix
            )
            offer.accept(offer.submission.submitted_by)

    def test_cannot_accept_already_accepted_offer(self):
        offer = ConditionalAssignmentOfferFactory(
            offered_until=fake.aware.date_time_this_year(
                before_now=False, after_now=True
            ),
            condition_details={
                "alternative_journal_id": self.submission.submitted_to.id
            },  # Hack temporary fix
        )
        offer.accept(offer.submission.submitted_by)
        with self.assertRaises(ValueError):
            offer.accept(offer.submission.submitted_by)

    def test_cannot_accept_declined_offer(self):
        offer = ConditionalAssignmentOfferFactory(
            offered_until=fake.aware.date_time_this_year(
                before_now=False, after_now=True
            ),
            status=ConditionalAssignmentOffer.STATUS_DECLINED,
            condition_details={
                "alternative_journal_id": self.submission.submitted_to.id
            },  # Hack temporary fix
        )
        with self.assertRaises(ValueError):
            offer.accept(offer.submission.submitted_by)

    def test_cannot_accept_later_identical_offer(self):
        offer = ConditionalAssignmentOfferFactory(
            offered_until=fake.aware.date_time_this_year(
                before_now=False, after_now=True
            ),
            condition_details={
                "alternative_journal_id": self.submission.submitted_to.id
            },  # Hack temporary fix
        )
        later_offer = ConditionalAssignmentOfferFactory(
            submission=offer.submission,
            offered_on=fake.aware.date_time_between(
                start_date=offer.offered_on, end_date="+30d"
            ),
            offered_until=offer.offered_until,
            condition_type=offer.condition_type,
            condition_details=offer.condition_details,
        )

        with self.assertRaises(ValueError):
            later_offer.accept(self.submission.submitted_by)
