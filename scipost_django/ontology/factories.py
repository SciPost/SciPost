__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from django.utils.text import slugify
import factory.fuzzy
from ontology.constants import TOPIC_RELATIONS_ASYM, TOPIC_RELATIONS_SYM
from ontology.models.relations import RelationAsym, RelationSym

from ontology.models.tag import Tag
from ontology.models.topic import Topic

from .models import Branch, AcademicField, Specialty
from common.faker import LazyObjectCount, LazyRandEnum, fake


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch
        django_get_or_create = ["name", "slug"]

    name = factory.LazyAttribute(lambda _: fake.word(part_of_speech="noun").title())
    slug = factory.LazyAttribute(lambda self: slugify(self.name.lower()))
    order = LazyObjectCount(Branch, offset=1)


class AcademicFieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcademicField
        django_get_or_create = ["name", "slug"]

    branch = factory.SubFactory(BranchFactory)
    name = factory.LazyAttribute(
        lambda self: f"{fake.word(part_of_speech='adjective').title()} {self.branch.name}"
    )
    slug = factory.LazyAttribute(lambda self: slugify(self.name))
    order = LazyObjectCount(AcademicField, offset=1)


class SpecialtyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Specialty
        django_get_or_create = ["name", "slug"]

    acad_field = factory.SubFactory(AcademicFieldFactory)
    name = factory.LazyAttribute(
        lambda _: f"{fake.word(part_of_speech='adjective').title()} {fake.word(part_of_speech='noun').title()}"
    )
    slug = factory.LazyAttribute(lambda self: slugify(self.name.lower()))
    order = LazyObjectCount(Specialty, offset=1)

    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for topic in extracted:
                self.topics.add(topic)

        self.topics.add(TopicFactory())


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic
        django_get_or_create = ["name", "slug"]

    name = factory.LazyAttribute(lambda _: fake.word(part_of_speech="noun").title())
    slug = factory.LazyAttribute(lambda self: slugify(self.name.lower()))

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)

        self.tags.add(TagFactory())


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ["name"]

    name = factory.LazyAttribute(lambda _: fake.word(part_of_speech="noun").title())


# Relations
class RelationAsymFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RelationAsym

    A = factory.SubFactory(TopicFactory)
    B = factory.SubFactory(TopicFactory)
    relation = LazyRandEnum(TOPIC_RELATIONS_ASYM)


class RelationSymFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RelationSym

    relation = LazyRandEnum(TOPIC_RELATIONS_SYM)

    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for topic in extracted:
                self.topics.add(topic)

        self.topics.add(*TopicFactory.create_batch(2))
