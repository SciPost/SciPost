__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import factory.fuzzy

from submissions.constants import EIC_REC_CHOICES, EIC_REC_STATUSES
from submissions.models import EICRecommendation

from common.faker import fake, LazyRandEnum


class EICRecommendationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EICRecommendation
        django_get_or_create = ("submission", "version")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    formulated_by = factory.SelfAttribute("submission.editor_in_charge")
    date_submitted = factory.LazyAttribute(
        lambda self: fake.aware.date_time_between(
            start_date=self.submission.submission_date, end_date="+1y"
        )
    )

    requested_changes = factory.Faker("paragraph")
    remarks_for_authors = factory.Faker("paragraph")
    remarks_for_editorial_college = factory.Faker("paragraph")

    for_journal = factory.SubFactory("journals.factories.JournalFactory")

    recommendation = LazyRandEnum(EIC_REC_CHOICES)
    status = LazyRandEnum(EIC_REC_STATUSES)

    version = factory.LazyAttribute(
        lambda self: 1
        + EICRecommendation.objects.filter(submission=self.submission).count()
    )
    active = True

    voting_deadline = factory.LazyAttribute(
        lambda self: fake.aware.date_time_between(
            start_date=self.date_submitted, end_date="+30d"
        )
    )

    # TODO: Add fields for the voting process
