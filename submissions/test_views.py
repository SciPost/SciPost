from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client

from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory
from scipost.models import Contributor

from .factories import EICassignedSubmissionFactory


class BaseContributorTestCase(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        ContributorFactory.create(
            user__username='Test',
            user__password='testpw'
        )


class PrefillUsingIdentifierTest(BaseContributorTestCase):
    def test_retrieving_existing_arxiv_paper(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1512.00030v1'})

        self.assertEqual(response.status_code, 200)

    def test_still_200_ok_if_identifier_is_wrong(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1512.00030'})

        self.assertEqual(response.status_code, 200)


class SubmitManuscriptTest(BaseContributorTestCase):
    def test_submit_correct_manuscript(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1512.00030v1'})

        params = response.context['form'].initial

        extras = {
            'discipline': 'physics',
            'submitted_to_journal': 'SciPost Physics',
            'submission_type': 'Article',
            'domain': 'T'
        }
        response = client.post(reverse('submissions:submit_manuscript'), {**params, **extras})

        self.assertEqual(response.status_code, 200)


class SubmissionDetailTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.submission = EICassignedSubmissionFactory()
        self.target = reverse(
            'submissions:submission',
            kwargs={'arxiv_identifier_w_vn_nr': self.submission.arxiv_identifier_w_vn_nr}
        )

    def test_status_code_200(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)
