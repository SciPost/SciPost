__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import random
import django
import factory

from common.faker import LazyAwareDate, LazyRandEnum, fake
from scipost.factories import ContributorFactory
from submissions.models.submission import Submission

from .models import CompetingInterest, RedFlag, SubmissionClearance


class CompetingInterestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CompetingInterest
        django_get_or_create = (
            "profile",
            "related_profile",
            "nature",
            "date_from",
            "date_until",
        )

    profile = factory.SubFactory("scipost.factories.ProfileFactory")
    related_profile = factory.SubFactory("scipost.factories.ProfileFactory")
    declared_by = factory.LazyAttribute(
        lambda self: ContributorFactory.from_profile(
            profile=random.choice([self.profile, self.related_profile])
        )
    )
    nature = LazyRandEnum(CompetingInterest.NATURE_CHOICES)
    date_from = factory.Faker("date_time_this_decade")
    date_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )

    comments = factory.Faker("text")


class SubmissionClearanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionClearance

    profile = factory.SubFactory("scipost.factories.ProfileFactory")
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    asserted_by = factory.SubFactory("scipost.factories.ContributorFactory")
    asserted_on = LazyAwareDate("date_time_this_decade")
    comments = factory.Faker("text")


class RedFlagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RedFlag
        abstract = True
        django_get_or_create = (
            "concerning_object_id",
            "concerning_object_type",
            "raised_by",
            "raised_on",
        )

    description = factory.Faker("text")
    raised_by = factory.SubFactory("scipost.factories.ContributorFactory")
    raised_on = LazyAwareDate("date_time_this_decade")


class SubmissionRedFlagFactory(RedFlagFactory):
    class Params:
        submission = factory.SubFactory("submissions.factories.SubmissionFactory")

    concerning_object_id = factory.SelfAttribute("submission.id")
    concerning_object_type = factory.LazyAttribute(
        lambda self: django.contrib.contenttypes.models.ContentType.objects.get_for_model(
            self.submission
        )
    )


class ProfileRedFlagFactory(RedFlagFactory):
    class Params:
        profile = factory.SubFactory("scipost.factories.ProfileFactory")

    concerning_object_id = factory.SelfAttribute("profile.id")
    concerning_object_type = factory.LazyAttribute(
        lambda self: django.contrib.contenttypes.models.ContentType.objects.get_for_model(
            self.profile
        )
    )
