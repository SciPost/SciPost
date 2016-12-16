from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from .views import RequestThesisLink
from scipost.factories import UserFactory
from .factories import ThesisLinkFactory
from .models import ThesisLink


class TestThesisDetail(TestCase):
    fixtures = ['groups', 'permissions']

    def test_visits_valid_thesis_detail(self):
        thesis_link = ThesisLinkFactory()
        client = Client()
        target = reverse('theses:thesis', kwargs={'thesislink_id': thesis_link.id})
        response = client.post(target)
        self.assertEqual(response.status_code, 200)


class TestRequestThesisLink(TestCase):
    fixtures = ['groups', 'permissions']

    def setUp(self):
        self.client = Client()

    def test_response_when_not_logged_in(self):
        '''A visitor that is not logged in cannot view this page.'''
        response = self.client.get(reverse('theses:request_thesislink'))
        self.assertEqual(response.status_code, 403)

    def test_response_when_logged_in(self):
        request = RequestFactory().get(reverse('theses:request_thesislink'))
        request.user = UserFactory()
        response = RequestThesisLink.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_redirects_to_acknowledgement_page(self):
        response = self.client.post(reverse('theses:request_thesislink'), {}, follow=True)
        self.assertRedirects(response, reverse('scipost:acknowledgement'))
