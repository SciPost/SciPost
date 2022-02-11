__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from django.utils.text import slugify

from scipost.models import Contributor

from .models import College, Fellowship


class CollegeFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    acad_field = factory.SubFactory("ontology.factories.AcademicFieldFactory")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    order = factory.Sequence(lambda n: College.objects.count() + 1)

    class Meta:
        model = College


class BaseFellowshipFactory(factory.django.DjangoModelFactory):
    contributor = factory.Iterator(Contributor.objects.all())
    start_date = factory.Faker("date_this_year")
    until_date = factory.Faker("date_between", start_date="now", end_date="+2y")

    guest = factory.Faker("boolean", chance_of_getting_true=10)

    class Meta:
        model = Fellowship
        django_get_or_create = ("contributor", "start_date")
        abstract = True


class FellowshipFactory(BaseFellowshipFactory):
    pass
