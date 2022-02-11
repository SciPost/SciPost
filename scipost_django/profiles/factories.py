__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from .models import Profile

from scipost.constants import TITLE_CHOICES


class ProfileFactory(factory.django.DjangoModelFactory):
    title = factory.Iterator(TITLE_CHOICES, getter=lambda c: c[0])
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    class Meta:
        model = Profile
