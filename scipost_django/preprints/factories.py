__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

import factory

from common.helpers import random_arxiv_identifier_with_version_number
from submissions.models.submission import Submission

from .models import Preprint

IDENTIFIER_VERSION_NUMBER_REGEX = r"v(\d{1,2})$"

class PreprintFactory(factory.django.DjangoModelFactory):
    identifier_w_vn_nr = factory.Faker("numerify", text="test_####.####")

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
            identifier_w_vn_nr=factory.Faker("numerify", text="scipost_######_#####"),
            _file=factory.django.FileField(filename="submission.pdf"),
        )

    @factory.post_generation
    def version_number(self, create, extracted, **kwargs):
        # Skip if the identifier already has a version number (e.g., arXiv-based ones)
        if re.search(IDENTIFIER_VERSION_NUMBER_REGEX, self.identifier_w_vn_nr):
            return

        if not create:
            return
        if extracted:
            if not isinstance(extracted, int):
                raise ValueError("Version number must be an integer.")
            if not (1 <= extracted <= 99):
                raise ValueError("Version number must be between 1 and 99.")

            version = extracted
        else:
            try:
                latest_submission = self.submission.get_latest_version()

                if latest_version_no := re.search(
                    IDENTIFIER_VERSION_NUMBER_REGEX,
                    latest_submission.preprint.identifier_w_vn_nr,
                ):
                    version = int(latest_version_no.group(1)) + 1
            except Submission.DoesNotExist:
                version = 1

        self.identifier_w_vn_nr += f"v{version}"
        self.save()