__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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

    for_journal = factory.SubFactory("journals.factories.JournalFactory")

    recommendation = LazyRandEnum(EIC_REC_PUBLICATION_CHOICES)
    status = LazyRandEnum(EIC_REC_STATUSES)

    version = factory.LazyAttribute(
        lambda self: 1
        + EICRecommendation.objects.filter(submission=self.submission).count()
    )
    active = True

    voting_deadline = LazyAwareDateOffset("date_submitted", "+30d")

    # TODO: Add fields for the voting process
