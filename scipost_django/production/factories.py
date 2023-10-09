__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
from django.db.models.signals import post_save

import factory

from production.constants import (
    PRODUCTION_EVENTS,
    PRODUCTION_STREAM_STATUS,
    PROOFS_REPO_STATUSES,
)
from production.models import (
    ProductionEvent,
    ProductionStream,
    ProductionUser,
    ProofsRepository,
)
from scipost.factories import UserFactory
from submissions.factories.submission import SubmissionFactory

from common.faker import LazyAwareDate, LazyRandEnum, fake

import datetime


class ProductionUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionUser

    user = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(
        lambda self: self.user.first_name + " " + self.user.last_name
    )


@factory.django.mute_signals(post_save)
class ProductionStreamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionStream

    submission = factory.SubFactory(SubmissionFactory)
    opened = LazyAwareDate("date_this_decade")
    closed = factory.LazyAttribute(
        # Random date between opened and 1 year later
        lambda self: self.opened
        + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 365),
        )
    )
    status = LazyRandEnum(PRODUCTION_STREAM_STATUS)
    officer = factory.SubFactory(ProductionUserFactory)
    supervisor = factory.SubFactory(ProductionUserFactory)
    invitations_officer = factory.SubFactory(ProductionUserFactory)
    on_hold = False
    # work_logs = factory.SubFactory(WorkLogFactory)


class ProductionEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionEvent

    stream = factory.SubFactory(ProductionStreamFactory)
    event = factory.Faker("random_element", elements=PRODUCTION_EVENTS)
    comments = factory.Faker("paragraph")
    noted_on = factory.Faker("past_date", start_date="-1y")
    noted_by = factory.LazyAttribute(
        lambda self: random.choice([self.stream.officer, self.stream.supervisor])
    )
    noted_to = factory.LazyAttribute(
        lambda self: random.choice([self.stream.officer, self.stream.supervisor])
    )
    duration = fake.duration()


class ProofsRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProofsRepository

    stream = factory.SubFactory(ProductionStreamFactory)
    status = LazyRandEnum(PROOFS_REPO_STATUSES)
    name = factory.LazyAttribute(
        lambda self: ProofsRepository._get_repo_name(self.stream)
    )
