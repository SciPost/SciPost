__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

import factory
import factory.fuzzy

from submissions.constants import EIC_REC_PUBLICATION_CHOICES, EIC_REC_STATUSES
from submissions.models import EICRecommendation

from common.faker import LazyAwareDateOffset, LazyRandEnum


class EICRecommendationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EICRecommendation
        django_get_or_create = ("submission", "version")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    formulated_by = factory.SelfAttribute("submission.editor_in_charge")
    date_submitted = LazyAwareDateOffset("submission.submission_date", "+1y")

    requested_changes = factory.Faker("paragraph")
    remarks_for_authors = factory.Faker("paragraph")
    remarks_for_editorial_college = factory.Faker("paragraph")

    for_journal = factory.SelfAttribute("submission.submitted_to")

    recommendation = LazyRandEnum(EIC_REC_PUBLICATION_CHOICES)
    status = LazyRandEnum(EIC_REC_STATUSES)

    version = factory.LazyAttribute(
        lambda self: 1
        + EICRecommendation.objects.filter(submission=self.submission).count()
    )
    active = True

    voting_deadline = LazyAwareDateOffset("date_submitted", "+30d")

    # TODO: Add fields for the voting process

    @factory.post_generation
    def eligible_to_vote(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.eligible_to_vote.set(extracted)
            return

        self.eligible_to_vote.set(
            list(
                self.submission.fellows.order_by("?")[
                    : random.randint(10, 20)
                ].values_list("contributor__id", flat=True)
            )
        )

    @factory.post_generation
    def voted(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            raise NotImplementedError("Manually setting votes is not implemented yet.")

        eligible_voters = list(
            self.eligible_to_vote.order_by("?").values_list("id", flat=True)
        )

        nr_journal_min = self.submission.submitted_to.minimal_nr_of_reports
        nr_eligible = len(eligible_voters)
        nr_for = random.randint(nr_journal_min, max(nr_journal_min, nr_eligible // 2))
        nr_against = random.randint(0, 1)
        nr_abstain = random.randint(0, 2)

        self.voted_for.set(eligible_voters[:nr_for])
        self.voted_against.set(eligible_voters[nr_for : nr_for + nr_against])
        self.voted_abstain.set(
            eligible_voters[nr_for + nr_against : nr_for + nr_against + nr_abstain]
        )