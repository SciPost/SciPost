__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.helpers import random_arxiv_identifier_with_version_number

from .models import Preprint


class PreprintFactory(factory.django.DjangoModelFactory):
    """
    Generate random Preprint instances.
    """

    identifier_w_vn_nr = factory.Sequence(
        lambda n: random_arxiv_identifier_with_version_number())
    url = factory.lazy_attribute(lambda o: (
        'https://arxiv.org/abs/%s' % o.identifier_w_vn_nr))

    class Meta:
        model = Preprint
