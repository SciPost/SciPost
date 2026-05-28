__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import factory.random

from common.faker import LazyAwareDateOffset, LazyRandEnum, fake

from ..models.assignment import *


class EditorialAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialAssignment
        django_get_or_create = ("submission", "to")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    to = factory.SubFactory("scipost.factories.ContributorFactory")
    status = LazyRandEnum(EditorialAssignment.ASSIGNMENT_STATUSES)

    date_created = LazyAwareDateOffset("submission.submission_date", "+30d")
    date_invited = LazyAwareDateOffset("date_created", "+30d")
    date_answered = LazyAwareDateOffset("date_invited", "+30d")


class ConditionalAssignmentOfferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConditionalAssignmentOffer
        django_get_or_create = ("submission", "offered_by")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    offered_by = factory.SubFactory("scipost.factories.ContributorFactory")
    offered_on = LazyAwareDateOffset("submission.submission_date", "+30d")
    offered_until = LazyAwareDateOffset("offered_on", "+30d")

    condition_type = LazyRandEnum(ConditionalAssignmentOffer.CONDITION_CHOICES)

    # Add parameter to accept the offer, in which case an acceptance date is set
    @factory.post_generation
    def accept(self, create, extracted, **kwargs):
        if extracted:
            self.status = ConditionalAssignmentOffer.STATUS_ACCEPTED
            self.accepted_on = self.offered_on + fake.time_delta("+10d")


class JournalTransferOfferFactory(ConditionalAssignmentOfferFactory):

    condition_type = "JournalTransfer"
    condition_details = factory.LazyAttribute(
        lambda self: {
            "alternative_journal_id": factory.random.random.choice(
                self.submission.submitted_to.alternative_journals.all()
            ).id
        }
    )
