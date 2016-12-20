import re

from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import Group
from django.urls import reverse

from .views import RequestThesisLink, VetThesisLinkRequests
from scipost.factories import UserFactory, ContributorFactory
from .factories import ThesisLinkFactory, VetThesisLinkFormFactory
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
        self.target = reverse('theses:request_thesislink')

    def test_response_when_not_logged_in(self):
        '''A visitor that is not logged in cannot view this page.'''
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 403)

    def test_response_when_logged_in(self):
        request = RequestFactory().get(self.target)
        request.user = UserFactory()
        response = RequestThesisLink.as_view()(request)
        self.assertEqual(response.status_code, 200)


class TestVetThesisLinkRequests(TestCase):
    fixtures = ['groups', 'permissions']

    def setUp(self):
        self.client = Client()
        self.target = reverse('theses:vet_thesislink_requests')

    def test_response_when_not_logged_in(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 403)

    def test_response_regular_contributor(self):
        '''
        A Contributor needs to be in the Vetting Editors group to be able to
        vet submitted thesis links.
        '''
        # Create ThesisLink to vet.
        ThesisLinkFactory()
        request = RequestFactory().get(self.target)
        user = UserFactory()
        request.user = user
        self.assertRaises(
            PermissionDenied, VetThesisLinkRequests.as_view(), request)

    def test_response_vetting_editor(self):
        # Create ThesisLink to vet.
        ThesisLinkFactory()
        request = RequestFactory().get(self.target)
        user = UserFactory()
        user.groups.add(Group.objects.get(name="Vetting Editors"))
        request.user = user
        response = VetThesisLinkRequests.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_thesislink_is_vetted_by_correct_contributor(self):
        # TODO: how to make sure we are vetting the right thesis link?
        contributor = ContributorFactory()
        contributor.user.groups.add(Group.objects.get(name="Vetting Editors"))
        post_data = VetThesisLinkFormFactory().data

        request = RequestFactory().post(self.target, post_data)
        request.user = contributor.user

        response = VetThesisLinkRequests.as_view()(request)

        self.assertTrue(False)
