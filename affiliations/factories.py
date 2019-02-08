__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from .constants import INSTITUTION_TYPES
from .models import Institution, Affiliation


class InstitutionFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('company')
    acronym = factory.lazy_attribute(lambda o: o.name[:16])
    country = factory.Faker('country_code')
    type = factory.Iterator(INSTITUTION_TYPES, getter=lambda c: c[0])

    class Meta:
        model = Institution
        django_get_or_create = ('name',)


class AffiliationFactory(factory.django.DjangoModelFactory):
    institution = factory.SubFactory('affiliations.factories.InstitutionFactory')
    contributor = factory.SubFactory('scipost.factories.ContributorFactory')
    begin_date = factory.Faker('date_this_decade')
    end_date = factory.Faker('future_date', end_date="+2y")

    class Meta:
        model = Affiliation
        django_get_or_create = ('institution', 'contributor')
