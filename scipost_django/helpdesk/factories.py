__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory
from django.utils.text import slugify
from django.utils.timezone import timedelta

from common.faker import LazyAwareDate, LazyRandEnum, fake

from .models import *


class QueueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Queue

    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda self: slugify(self.name.lower()))
    description = factory.Faker("text")
    managing_group = factory.SubFactory("scipost.factories.GroupFactory")
    parent_queue = None

    @factory.post_generation
    def response_groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.response_groups.add(group)


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket

    queue = factory.SubFactory(QueueFactory)
    title = factory.Faker("sentence")
    description = factory.Faker("text")
    publicly_visible = False
    defined_on = LazyAwareDate("date_time_this_decade")
    defined_by = factory.SubFactory("scipost.factories.UserFactory")
    deadline = factory.LazyAttribute(
        lambda self: fake.aware.date_time_between(
            start_date=self.defined_on, end_date="+1y"
        )
    )
    priority = LazyRandEnum(TICKET_PRIORITIES)
    status = LazyRandEnum(TICKET_STATUSES)
    assigned_to = factory.SubFactory("scipost.factories.UserFactory")
