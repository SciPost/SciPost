__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.helpers import random_arxiv_identifier_with_version_number

from .models import Preprint


class PreprintFactory(factory.django.DjangoModelFactory):
    identifier_w_vn_nr = factory.Faker("numerify", text="####.####")

    class Meta:
        model = Preprint
        django_get_or_create = ("identifier_w_vn_nr",)

    class Params:
        arXiv = factory.Trait(
            identifier_w_vn_nr=random_arxiv_identifier_with_version_number(),
            url=factory.LazyAttribute(
                lambda self: f"https://arxiv.org/abs/{self.identifier_w_vn_nr}"
            ),
        )
        scipost = factory.Trait(
            identifier_w_vn_nr=factory.Faker("numerify", text="scipost_######_#####v#"),
            _file=factory.django.FileField(filename="submission.pdf"),
        )
