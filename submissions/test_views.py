from django.test import TestCase
from django.test import Client
import pprint
from submissions.views import *



class PrefillUsingIdentifierTest(TestCase):
    fixtures = ['permissions', 'groups', 'contributors']

    def test_retrieving_existing_arxiv_paper(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post('/submissions/prefill_using_identifier',
                               {'identifier': '1512.00030v1'})

        self.assertEqual(response.status_code, 200)

    def test_still_200_ok_if_identifier_is_wrong(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post('/submissions/prefill_using_identifier',
                               {'identifier': '1512.00030'})

        self.assertEqual(response.status_code, 200)

class SubmitManuscriptTest(TestCase):
    fixtures = ['permissions', 'groups', 'contributors']

    def test_submit_correct_manuscript(self):
        client = Client()
        client.login(username="Test", password="testpw")

        response = client.post('/submissions/prefill_using_identifier',
                               {'identifier': '1512.00030v1'})

        params = response.context['form'].initial

        extras = {'discipline': 'physics',
                  'submitted_to_journal': 'SciPost Physics',
                  'submission_type': 'Article',
                  'domain': 'T'}
        response = client.post('/submissions/submit_manuscript',
                               {**params, **extras})

        pprint.pprint(params)
        self.assertEqual(response.status_code, 200)
