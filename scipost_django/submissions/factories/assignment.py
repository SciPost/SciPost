__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import factory.random

from common.faker import LazyRandEnum, fake

from ..models.assignment import *


class EditorialAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialAssignment
        django_get_or_create = ("submission", "to")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    to = factory.SubFactory("scipost.factories.ContributorFactory")
    status = LazyRandEnum(EditorialAssignment.ASSIGNMENT_STATUSES)

    date_created = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.submission.submission_date, end_date="+60d"
        )
    )
    date_invited = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.date_created, end_date="+10d"
        )
    )
    date_answered = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.date_invited, end_date="+10d"
        )
    )


class ConditionalAssignmentOfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConditionalAssignmentOffer
        django_get_or_create = ("submission", "offered_by")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    offered_by = factory.SubFactory("scipost.factories.ContributorFactory")
    offered_on = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.submission.submission_date, end_date="+60d"
        )
    )
    offered_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.offered_on, end_date="+30d"
        )
    )

    condition_type = LazyRandEnum(ConditionalAssignmentOffer.CONDITION_CHOICES)

    # Add parameter to accept the offer, in which case an acceptance date is set
    @factory.post_generation
    def accept(self, create, extracted, **kwargs):
        if extracted:
            self.status = ConditionalAssignmentOffer.STATUS_ACCEPTED
            self.accepted_on = fake.aware.date_between(
                start_date=self.offered_on, end_date="+10d"
            )


class JournalTransferOfferFactory(ConditionalAssignmentOfferFactory):

    condition_type = "JournalTransfer"
    condition_details = factory.LazyAttribute(
        lambda self: {
            "alternative_journal_id": factory.random.random.choice(
                self.submission.submitted_to.alternative_journals.all()
            ).id
        }
    )
