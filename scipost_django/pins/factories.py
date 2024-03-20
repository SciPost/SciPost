__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.models import ContentType
import factory

from finances.models.subsidy import Subsidy
from .models import *
from common.faker import LazyRandEnum, fake, LazyAwareDate


class BaseNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    class Params:
        regarding_object = factory.Trait(
            regarding_content_type=factory.SelfAttribute("content_type"),
            regarding_object_id=factory.SelfAttribute("object_id"),
        )

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text")
    visibility = LazyRandEnum(Note.VISIBILITY_CHOICES)
    author = factory.SubFactory("scipost.factories.ContributorFactory")
    created = factory.Faker("date_time_this_year")
    modified = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.created, end_date="+1y")
    )


class BasePinFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pin

    note = factory.SubFactory(BaseNoteFactory)
    user = factory.SubFactory("scipost.factories.UserFactory")
    due_date = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.note.created, end_date="+1y"
        )
    )
