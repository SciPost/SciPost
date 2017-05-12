from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client

from common.helpers.test import add_groups_and_permissions
from scipost.factories import ContributorFactory
# from scipost.models import Contributor

from .constants import STATUS_UNASSIGNED
from .factories import EICassignedSubmissionFactory
from .forms import SubmissionForm, SubmissionIdentifierForm
from .models import Submission


class BaseContributorTestCase(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        ContributorFactory.create(
            user__username='Test',
            user__password='testpw'
        )


class PrefillUsingIdentifierTest(BaseContributorTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('submissions:prefill_using_identifier')
        self.assertTrue(self.client.login(username="Test", password="testpw"))

    def test_basic_responses(self):
        # Test anonymous client is rejected
        client = Client()
        response = client.get(self.url)
        self.assertEqual(response.status_code, 403)
        response = client.post(self.url, {'identifier': '1512.00030v1'})
        self.assertEqual(response.status_code, 403)

        # Registered Contributor should get 200
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retrieving_existing_arxiv_paper(self):
        '''Test view with a valid post request.'''
        response = self.client.post(self.url, {'identifier': '1512.00030v1'})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SubmissionForm)
        self.assertIsInstance(response.context['identifierform'], SubmissionIdentifierForm)
        self.assertTrue(response.context['identifierform'].is_valid())

    def test_still_200_ok_if_identifier_is_wrong(self):
        response = self.client.post(self.url, {'identifier': '1512.00030'})
        self.assertEqual(response.status_code, 200)


class SubmitManuscriptTest(BaseContributorTestCase):
    def test_submit_correct_manuscript(self):
        client = Client()

        # Unauthorized request shouldn't be possible
        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1512.00030v1'})
        self.assertEquals(response.status_code, 403)

        # Registered Contributor should get 200
        self.assertTrue(client.login(username="Test", password="testpw"))
        response = client.post(reverse('submissions:prefill_using_identifier'),
                               {'identifier': '1512.00030v1'})
        self.assertEqual(response.status_code, 200)

        # Fill form parameters
        params = response.context['form'].initial
        params.update({
            'discipline': 'physics',
            'submitted_to_journal': 'SciPost Physics',
            'submission_type': 'Article',
            'domain': 'T'
        })
        response = client.post(reverse('submissions:submit_manuscript'), **params)

        self.assertEqual(response.status_code, 200)
        # submission = Submission.objects.filter(status=STATUS_UNASSIGNED).last()
        # raise Exception(response.content)
        # self.assertIn(submission, response.context)


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
