__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz

from faker import Faker

from submissions.constants import REPORT_REC
from submissions.models import Submission, EICRecommendation


class EICRecommendationFactory(factory.django.DjangoModelFactory):
    submission = factory.Iterator(Submission.objects.all())
    date_submitted = factory.lazy_attribute(
        lambda o: Faker().date_time_between(
            start_date=o.submission.submission_date, end_date="now", tzinfo=pytz.UTC
        )
    )
    remarks_for_authors = factory.Faker("paragraph")
    requested_changes = factory.Faker("paragraph")
    remarks_for_editorial_college = factory.Faker("paragraph")
    recommendation = factory.Iterator(REPORT_REC[1:], getter=lambda c: c[0])
    version = 1
    active = True

    class Meta:
        model = EICRecommendation
