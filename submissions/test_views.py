from django.test import TestCase
from django.test import Client

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
