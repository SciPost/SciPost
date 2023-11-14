import factory
from common import faker
from common.faker import LazyRandEnum
from organizations.constants import ORGANIZATION_STATUSES, ORGANIZATION_TYPES
from organizations.models import Organization


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ("name", "acronym")

    class Params:
        language = "en_US"

    orgtype = LazyRandEnum(ORGANIZATION_TYPES)
    status = LazyRandEnum(ORGANIZATION_STATUSES)
    name = factory.Faker("company")
    name_original = factory.lazy_attribute(
        lambda self: faker.Faker(locale=self.language).company()
    )
    acronym = factory.LazyAttribute(
        lambda self: "".join(w[0].upper() for w in self.name.split())
    )
    country = factory.Faker("country_code")
    address = factory.Faker("address")
    logo = factory.django.ImageField()
    css_class = ""
    grid_json = {}
    crossref_json = {}
    parent = None
    superseded_by = None
    cf_associated_publication_ids = {}
    cf_nr_associated_publications = 0
    cf_balance_info = {}
    cf_expenditure_for_publication = {}
