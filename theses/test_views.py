from django.test import TestCase
from django.test.client import Client


class TestThesisDetail(TestCase):

    def test_acknowledges_after_submitting_comment(self):
        client = Client()
        response = client.post('/theses/1')
        self.assertEqual(response.get('location'), 'bladiebla')
