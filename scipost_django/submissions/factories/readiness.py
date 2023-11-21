__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory
from ..models import Readiness

from common.faker import LazyRandEnum, fake


class ReadinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Readiness
        django_get_or_create = ("submission", "fellow")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    fellow = factory.SubFactory("colleges.factories.FellowshipFactory")
    status = LazyRandEnum(Readiness.STATUS_CHOICES)
    comments = factory.Faker("paragraph")
    datetime = factory.LazyAttribute(
        lambda self: fake.aware.date_time_between(
            start_date=self.submission.submission_date, end_date="+2M"
        )
    )
