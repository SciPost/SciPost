import factory

from scipost.models import Contributor

from .models import Fellowship


class BaseFellowshipFactory(factory.django.DjangoModelFactory):
    contributor = factory.Iterator(Contributor.objects.all())
    start_date = factory.Faker('date_this_year')
    until_date = factory.Faker('date_between', start_date="now", end_date="+2y")

    guest = factory.Faker('boolean', chance_of_getting_true=10)

    class Meta:
        model = Fellowship
        django_get_or_create = ('contributor', 'start_date')
        abstract = True


class FellowshipFactory(BaseFellowshipFactory):
    pass
