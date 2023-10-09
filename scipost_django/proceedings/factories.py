__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

import factory
from journals.factories import IssueFactory
from proceedings.models import Proceedings
import datetime


class ProceedingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proceedings

    issue = factory.SubFactory(IssueFactory)
    event_name = factory.Faker("company")
    event_suffix = factory.Faker("company_suffix")
    event_description = factory.Faker("paragraph")
    event_start_date = factory.Faker("date_this_decade")
    event_end_date = factory.LazyAttribute(
        lambda self: self.event_start_date
        + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 365),
        )
    )

    submissions_open = factory.Faker("date_this_decade")
    submissions_close = factory.LazyAttribute(
        lambda self: self.submissions_open
        + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 365),
        )
    )
    submissions_deadline = factory.LazyAttribute(
        lambda self: self.submissions_close
        + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 365),
        )
    )

    preface_title = factory.Faker("sentence")
    preface_text = factory.Faker("paragraph")
