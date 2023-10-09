__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

import factory
from faker import Faker
from faker.providers import BaseProvider


class LazyRandEnum(factory.LazyAttribute):
    """
    Define a lazy attribute that takes a random value from a Django enum.
    The Django enum is a list of two-tuples, where the first element is the
    value and the second element is the human-readable name.
    The attribute evalutates to the value, not the human-readable name.
    """

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        super().__init__(function=self._random_choice_from_enum, *args, **kwargs)

    def _random_choice_from_enum(self, _):
        return random.choice(self.enum)[0]


class LazyAwareDate(factory.LazyAttribute):
    """
    Define a lazy attribute that returns a timezone-aware random date from a Faker provider.
    """

    def __init__(self, provider, *args, **kwargs):
        self.provider = provider

        super().__init__(function=lambda _: self.generate_aware_date(*args, **kwargs))

    def _generate_date(self, *args, **kwargs):
        return getattr(fake, self.provider)(*args, **kwargs)

    @staticmethod
    def _convert_to_datetime(date):
        return datetime.combine(date, datetime.min.time())

    def generate_aware_date(self, *args, **kwargs):
        return make_aware(
            self._convert_to_datetime(self._generate_date(*args, **kwargs))
        )


class DurationProvider(BaseProvider):
    def duration(self):
        seconds = self.random_int(min=0, max=86400)
        return timedelta(seconds=seconds)


fake = Faker()
fake.add_provider(DurationProvider)
