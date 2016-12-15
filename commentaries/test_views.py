from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test import Client, TestCase

# from .views import request_commentary

class RequestCommentaryTest(TestCase):
    """Test cases for request_commentary view method"""
    # fixtures = ['permissions', 'groups', 'contributors']

    def setUp(self):
        self.client = Client()
        self.client.login(username="feynman", password="richard")
        self.url = reverse('commentaries:request_commentary')

    def test_get_request(self):
        # contributor_group = Group.objects.get_or_create(name='Registered Contributors')
        # self.contributor_group
        request = self.client.get(self.url)

        self.user.user_permissions.add('scipost.can_request_commentary_pages')

        # Request succesfull
        self.assertEquals(
            request.status_code, 200,
            'Get request on request_commentary has failed')
