__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
from common.faker import LazyRandEnum
from scipost.constants import TITLE_CHOICES

from .models import Profile


class ProfileFactory(factory.django.DjangoModelFactory):
    title = LazyRandEnum(TITLE_CHOICES)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    class Meta:
        model = Profile
