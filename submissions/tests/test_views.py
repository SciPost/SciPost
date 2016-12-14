from django.test import TestCase
from django.test import Client

from submissions.views import *

print('Hi')


class PrefillUsingIdentifierTest(TestCase):
    def test_retrieving_arxiv_paper(self):
        # Create an instance of a GET request.
        # request = self.factory.post('/submissions/prefill_using_identifier',
        #                             {'identifier': '1512.00030v1'})

        client = Client()
        client.login()

        response = client.post('/submissions/prefill_using_identifier',
                               {'identifier': '1512.00030v1'})

        self.assertEqual(response.status_code, 200)
