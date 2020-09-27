__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from django.utils.text import slugify

from .models import Branch, AcademicField, Specialty


class BranchFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda b: 'Branch %d' % b.order)
    slug = factory.LazyAttribute(lambda b: slugify('branch-%d' % b.order))
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Branch


class AcademicFieldFactory(factory.django.DjangoModelFactory):
    branch = factory.SubFactory(BranchFactory)
    name = factory.LazyAttribute(lambda b: 'Field %d' % b.order)
    slug = factory.LazyAttribute(lambda b: slugify('field-%d' % b.order))
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = AcademicField


class SpecialtyFactory(factory.django.DjangoModelFactory):
    acad_field = factory.SubFactory(AcademicField)
    name = factory.LazyAttribute(lambda b: 'Specialty %d' % b.order)
    slug = factory.LazyAttribute(lambda b: slugify('specialty-%d' % b.order))
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Specialty
