__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

import factory
from common.faker import LazyRandEnum, fake
from ontology.factories import SpecialtyFactory, TopicFactory
from profiles.constants import AFFILIATION_CATEGORIES, PROFILE_NON_DUPLICATE_REASONS
from scipost.constants import TITLE_CHOICES

from .models import *


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile
        django_get_or_create = ("orcid_id",)

    title = LazyRandEnum(TITLE_CHOICES)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    orcid_id = factory.Faker("numerify", text="####-####-####-####")
    webpage = factory.Faker("url")
    acad_field = factory.SubFactory("ontology.factories.AcademicFieldFactory")

    @factory.post_generation
    def specialties(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for specialty in extracted:
                self.specialties.add(specialty)
        else:
            self.specialties.add(
                *SpecialtyFactory.create_batch(
                    random.randint(1, 3), acad_field=self.acad_field
                )
            )

    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for topic in extracted:
                self.topics.add(topic)
        else:
            self.topics.add(*TopicFactory.create_batch(random.randint(1, 3)))


class ProfileNonDuplicatesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfileNonDuplicates

    reason = LazyRandEnum(PROFILE_NON_DUPLICATE_REASONS)

    @factory.post_generation
    def profiles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for profile in extracted:
                self.profiles.add(profile)
        else:
            self.profiles.add(*ProfileFactory.create_batch(random.randint(1, 3)))


class ProfileEmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfileEmail

    profile = factory.SubFactory(ProfileFactory)
    email = factory.Faker("email")


class AffiliationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Affiliation

    profile = factory.SubFactory(ProfileFactory)
    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    category = LazyRandEnum(AFFILIATION_CATEGORIES)
    description = factory.Faker("sentence")
    date_from = factory.Faker("date_this_decade")
    date_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )
