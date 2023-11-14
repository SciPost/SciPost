__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import random
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

import factory
from faker import Faker
from faker.providers import BaseProvider
import pytz


class LazyRandEnum(factory.LazyAttribute):
    """
    Define a lazy attribute that takes a random value from a Django enum.
    The Django enum is a list of two-tuples, where the first element is the
    value and the second element is the human-readable name.
    The attribute evalutates to the value, not the human-readable name.
    """

    def __init__(self, enum, repeat=1, *args, **kwargs):
        self.enum = enum
        self.repeat = repeat
        super().__init__(function=self._random_choice_from_enum, *args, **kwargs)

    def _random_choice_from_enum(self, _):
        if self.repeat == 1:
            return random.choice(self.enum)[0]
        else:
            return [random.choice(self.enum)[0] for _ in range(self.repeat)]


class LazyObjectCount(factory.LazyAttribute):
    """
    Define a lazy attribute that returns the total number of objects of a model.
    """

    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.offset = kwargs.pop("offset", 0)

        super().__init__(function=self._get_object_count, *args, **kwargs)

    def _get_object_count(self, _):
        return self.model.objects.count() + self.offset


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


class TZAwareDateAccessor:
    """
    Accessor to modify providers to return timezone-aware dates.
    """

    def __init__(self, parent_obj):
        def aware_wrapper(func):
            def wrapper(*args, **kwargs):
                faker_date = func(*args, **kwargs)
                faker_datetime = datetime.combine(faker_date, datetime.min.time())

                return make_aware(faker_datetime, timezone=pytz.utc)

            return wrapper

        # create a new attribute on self for each method of parent object
        # where each attribute is a method that returns a timezone-aware date
        for attr in dir(parent_obj):
            if attr.startswith("date"):
                setattr(self, attr, aware_wrapper(func=getattr(parent_obj, attr)))


fake = Faker()
fake.add_provider(DurationProvider)

aware_date_accessor = TZAwareDateAccessor(fake)
fake.aware = aware_date_accessor
