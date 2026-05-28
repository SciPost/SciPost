__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random
import django
import factory

from common.faker import LazyAwareDate, LazyAwareDateOffset, LazyRandEnum
from scipost.factories import ContributorFactory

from .models import ConflictOfInterest, RedFlag, SubmissionClearance


class ConflictOfInterestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConflictOfInterest
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
        lambda self: ContributorFactory(
            profile=random.choice([self.profile, self.related_profile])
        )
    )
    nature = LazyRandEnum(ConflictOfInterest.NATURE_CHOICES)
    date_from = factory.Faker("date_time_this_decade")
    date_until = LazyAwareDateOffset("date_from", "+1y")

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
