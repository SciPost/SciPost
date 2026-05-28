__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random
import re

import factory
from common.faker import LazyAwareDateOffset, LazyRandEnum, fake
from common.utils.text import latinise
from ontology.factories import SpecialtyFactory, TopicFactory
from profiles.constants import AFFILIATION_CATEGORIES
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

    class Params:
        registered = factory.Trait(
            contributor=factory.SubFactory("scipost.factories.ContributorFactory"),
        )

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

    @factory.post_generation
    def emails(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for i, email in enumerate(extracted):
                ProfileEmailFactory(profile=self, email=email, primary=(i == 0))
        else:
            try:
                ProfileEmailFactory(
                    profile=self, email=self.contributor.user.email, primary=True
                )
            except Contributor.DoesNotExist:
                ProfileEmailFactory(profile=self, primary=True)


class ProfileEmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfileEmail

    profile = factory.SubFactory(ProfileFactory)
    email = factory.LazyAttribute(
        lambda self: "{first_name[0]}{last_name}{num}@example.com".format(
            first_name=re.sub(r"[\W\s]", "", latinise(self.profile.first_name.lower())),
            last_name=re.sub(r"[\W\s]", "", latinise(self.profile.last_name.lower())),
            num=fake.random_number(digits=4, fix_len=True),
        )
    )


class AffiliationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Affiliation

    profile = factory.SubFactory(ProfileFactory)
    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    category = LazyRandEnum(AFFILIATION_CATEGORIES)
    description = factory.Faker("sentence")
    date_from = factory.Faker("date_this_decade")
    date_until = LazyAwareDateOffset("date_from", "+1y")