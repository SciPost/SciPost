__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
from django.db.models.signals import post_save

import factory
from common.faker import LazyAwareDate, LazyRandEnum, fake

from production.constants import (
    PRODUCTION_EVENTS,
    PRODUCTION_STREAM_STATUS,
    PROOFS_REPO_STATUSES,
    PROOFS_STATUSES,
)
from finances.factories import ProductionStreamWorkLogFactory
from scipost.factories import UserFactory
from submissions.factories.submission import SubmissionFactory

from .models import *


class ProductionUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionUser
        django_get_or_create = ("user",)

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
        lambda self: fake.aware.date_between(start_date=self.opened, end_date="+1y")
    )
    status = LazyRandEnum(PRODUCTION_STREAM_STATUS)
    officer = factory.SubFactory(ProductionUserFactory)
    supervisor = factory.SubFactory(ProductionUserFactory)
    invitations_officer = factory.SubFactory(ProductionUserFactory)
    on_hold = False

    @factory.post_generation
    def work_logs(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for work_log in extracted:
                self.work_logs.add(work_log)

        else:
            self.work_logs.add(
                *ProductionStreamWorkLogFactory.create_batch(
                    random.randint(1, 4),
                    stream=self,
                    user=random.choice([self.officer.user, self.supervisor.user]),
                )
            )


class ProductionEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionEvent

    stream = factory.SubFactory(ProductionStreamFactory)
    event = factory.Faker("random_element", elements=PRODUCTION_EVENTS)
    comments = factory.Faker("paragraph")
    noted_on = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.stream.opened,
            end_date=self.stream.closed,
        )
    )
    noted_by = factory.LazyAttribute(
        lambda self: random.choice([self.stream.officer, self.stream.supervisor])
    )
    noted_to = factory.LazyAttribute(
        lambda self: random.choice([self.stream.officer, self.stream.supervisor])
    )
    duration = fake.duration()


class ProductionEventAttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductionEventAttachment

    production_event = factory.SubFactory(ProductionEventFactory)
    attachment = factory.django.FileField(filename="author_comments.pdf")


class ProofsRepositoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProofsRepository
        django_get_or_create = ("stream",)

    stream = factory.SubFactory(ProductionStreamFactory)
    status = LazyRandEnum(PROOFS_REPO_STATUSES)
    name = factory.LazyAttribute(
        lambda self: ProofsRepository._get_repo_name(self.stream)
    )


class ProofsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proofs

    attachment = factory.django.FileField(filename="proofs.pdf")
    stream = factory.SubFactory(ProductionStreamFactory)
    uploaded_by = factory.LazyAttribute(lambda self: self.stream.officer)
    created = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.stream.opened,
            end_date=self.stream.closed,
        )
    )
    status = LazyRandEnum(PROOFS_STATUSES)
