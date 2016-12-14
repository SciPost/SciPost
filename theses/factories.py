import factory
from . import models


class ThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ThesisLink

    vetted = True
    type = models
