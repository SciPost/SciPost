__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase
from ..factories import PreprintFactory


class TestPreprintFactory(TestCase):
    def test_can_create_preprints(self):
        preprint = PreprintFactory()
        self.assertIsNotNone(preprint)

    def test_can_create_arxiv_preprints(self):
        preprint = PreprintFactory(arXiv=True)
        self.assertIsNotNone(preprint)
        self.assertTrue(preprint.url.startswith("https://arxiv.org/abs/"))

    def test_can_create_scipost_preprints(self):
        preprint = PreprintFactory(scipost=True)
        self.assertIsNotNone(preprint)
        self.assertTrue(preprint.identifier_w_vn_nr.startswith("scipost_"))
