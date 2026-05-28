__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory

from .models import *

from common.faker import LazyAwareDateOffset, LazyRandEnum


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
    modified = LazyAwareDateOffset("created", "+1y")


class BasePinFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pin

    note = factory.SubFactory(BaseNoteFactory)
    user = factory.SubFactory("scipost.factories.UserFactory")
    due_date = LazyAwareDateOffset("note.created", "+1y")
