__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
import factory

from finances.models import WorkLog
from production.constants import PRODUCTION_ALL_WORK_LOG_TYPES
from scipost.factories import UserFactory

from common.faker import LazyRandEnum, fake


class WorkLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkLog

    user = factory.SubFactory(UserFactory)
    comments = factory.Faker("paragraph")
    log_type = LazyRandEnum(PRODUCTION_ALL_WORK_LOG_TYPES)
    duration = factory.LazyAttribute(lambda _: fake.duration())
    work_date = factory.Faker("date_this_year")
    created = factory.Faker("past_date", start_date="-1y")

    content_type = None
    object_id = None
    content = None
