__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
from django.utils.text import slugify

from .models import *


class MailingListFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MailingList

    name = factory.Faker("word")
    slug = factory.LazyAttribute(lambda self: slugify(self.name))

    is_opt_in = False

    @factory.post_generation
    def eligible_subscribers(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contributor in extracted:
                self.eligible_subscribers.add(contributor)

    @factory.post_generation
    def subscribed(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contributor in extracted:
                self.subscribed.add(contributor)
