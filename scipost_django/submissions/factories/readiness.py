__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory
from ..models import Readiness

from common.faker import LazyAwareDateOffset, LazyRandEnum


class ReadinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Readiness
        django_get_or_create = ("submission", "fellow")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    fellow = factory.SubFactory("colleges.factories.ContributorFactory")
    status = LazyRandEnum(Readiness.STATUS_CHOICES)
    comments = factory.Faker("paragraph")
    datetime = LazyAwareDateOffset("submission.submission_date", "+2M")
