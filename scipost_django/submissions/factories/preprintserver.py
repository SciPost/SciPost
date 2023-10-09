__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from faker import Faker

from submissions.models.preprint_server import PreprintServer


class PreprintServerFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("sentence")
    url = factory.Faker("url")

    class Meta:
        model = PreprintServer

    @classmethod
    def arxiv(cls):
        return cls(name="arXiv", url="https://arxiv.org/")
