import factory
import faker

from common.faker import LazyAwareDate, LazyRandEnum, fake
from organizations.constants import (
    ORGANIZATION_EVENTS,
    ORGANIZATION_STATUSES,
    ORGANIZATION_TYPES,
    ROLE_KINDS,
)
from organizations.models import (
    Contact,
    ContactPerson,
    ContactRole,
    Organization,
    OrganizationEvent,
    OrganizationLogo,
)
from scipost.constants import TITLE_CHOICES


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
    ror_json = {}
    crossref_json = {}
    parent = None
    superseded_by = None


class OrganizationLogoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationLogo

    organization = factory.SubFactory(OrganizationFactory)
    image = factory.django.ImageField()
    mimetype = LazyRandEnum(OrganizationLogo.MIMETYPE_CHOICES)
    width = factory.Faker("pyint")
    height = factory.Faker("pyint")
    order = factory.Sequence(lambda n: n)


class OrganizationEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationEvent

    organization = factory.SubFactory(OrganizationFactory)
    event = LazyRandEnum(ORGANIZATION_EVENTS)
    comments = factory.Faker("text")
    noted_on = LazyAwareDate("date_this_year")
    noted_by = factory.SubFactory("scipost.factories.UserFactory")


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    user = factory.SubFactory("scipost.factories.UserFactory")
    title = factory.SelfAttribute("user.contributor.profile.title")
    activation_key = factory.SelfAttribute("user.contributor.activation_key")
    key_expires = factory.SelfAttribute("user.contributor.key_expires")


class ContactRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactRole

    contact = factory.SubFactory(ContactFactory)
    organization = factory.SubFactory(OrganizationFactory)
    kind = LazyRandEnum(ROLE_KINDS, repeat=2)
    date_from = LazyAwareDate("date_this_year")
    date_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )


class ContactPersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactPerson

    organization = factory.SubFactory(OrganizationFactory)
    title = LazyRandEnum(TITLE_CHOICES)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    role = factory.Faker("job")
