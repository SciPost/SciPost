__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
from common.faker import LazyAwareDateOffset
from django.utils.text import slugify
from journals.factories import JournalFactory

from .models import *


class SeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Series

    name = factory.Faker("sentence", nb_words=4)
    slug = factory.LazyAttribute(lambda self: slugify(self.name))
    description = factory.Faker("paragraph")
    information = factory.Faker("paragraph")
    image = factory.django.ImageField()

    @factory.post_generation
    def container_journals(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for journal in extracted:
                self.container_journals.add(journal)
        else:
            self.container_journals.add(JournalFactory())


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    series = factory.SubFactory(SeriesFactory)
    name = factory.Faker("sentence", nb_words=4)
    slug = factory.LazyAttribute(lambda self: slugify(self.name))

    description = factory.Faker("paragraph")
    event_details = factory.Faker("paragraph")

    event_start_date = factory.Faker("date_this_decade")
    event_end_date = LazyAwareDateOffset("event_start_date", "+1y")

    image = factory.django.ImageField()
