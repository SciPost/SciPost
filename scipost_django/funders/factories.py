__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
from .models import *
import factory


class FunderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Funder

    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    name = factory.SelfAttribute("organization.name")
    acronym = factory.SelfAttribute("organization.acronym")
    identifier = factory.Faker("numerify", text="http://dx.doi.org/10.#####/#########")


class GrantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Grant

    funder = factory.SubFactory(FunderFactory)
    number = factory.Faker("isbn10")
    recipient = factory.SubFactory("scipost.factories.ContributorFactory")
    recipient_name = factory.SelfAttribute("recipient.profile.full_name")
    further_details = factory.Faker("text")
