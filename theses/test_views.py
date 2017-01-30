import re

from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import Group
from django.urls import reverse, reverse_lazy
from django.contrib.messages.storage.fallback import FallbackStorage

from scipost.factories import UserFactory, ContributorFactory
from comments.factories import CommentFactory
from comments.forms import CommentForm
from comments.models import Comment
from .views import RequestThesisLink, VetThesisLinkRequests, thesis_detail
from .factories import ThesisLinkFactory, VetThesisLinkFormFactory
from .models import ThesisLink
from common.helpers import model_form_data


class TestThesisDetail(TestCase):
    fixtures = ['groups', 'permissions']

    def test_visits_valid_thesis_detail(self):
        """ A visitor does not have to be logged in to view a thesis link. """
        thesis_link = ThesisLinkFactory()
        client = Client()
        target = reverse('theses:thesis', kwargs={'thesislink_id': thesis_link.id})
        response = client.post(target)
        self.assertEqual(response.status_code, 200)

    def test_submitting_comment_creates_comment(self):
        """ Valid Comment gets saved """

        contributor = ContributorFactory()
        thesislink = ThesisLinkFactory()
        valid_comment_data = model_form_data(CommentFactory.build(), CommentForm)
        target = reverse('theses:thesis', kwargs={'thesislink_id': thesislink.id})

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        request.user = contributor.user
        response = thesis_detail(request, thesislink_id=thesislink.id)

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 1)


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
        thesis_link = ThesisLinkFactory()
        contributor = ContributorFactory()
        contributor.user.groups.add(Group.objects.get(name="Vetting Editors"))
        post_data = VetThesisLinkFormFactory().data
        target = reverse('theses:vet_thesislink_request', kwargs={'thesislink_id': thesis_link.id})

        request = RequestFactory().post(target, post_data)
        request.user = contributor.user

        # I don't know what the following three lines do, but they help make a RequestFactory
        # work with the messages middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = VetThesisLinkRequests.as_view()(request, thesislink_id=thesis_link.id)
        self.assertEqual(thesis_link.vetted_by, contributor)
