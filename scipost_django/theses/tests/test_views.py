__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django.core import mail
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
from ..views import RequestThesisLink, VetThesisLink, thesis_detail
from ..factories import ThesisLinkFactory, ThesisLinkFactory, VetThesisLinkFormFactory
from ..models import ThesisLink
from ..forms import VetThesisLinkForm
from common.helpers import model_form_data
from common.helpers.test import add_groups_and_permissions


class TestThesisDetail(TestCase):
    def setUp(self):
        add_groups_and_permissions()

    def test_visits_valid_thesis_detail(self):
        """A visitor does not have to be logged in to view a thesis link."""
        thesis_link = ThesisLinkFactory()
        client = Client()
        target = reverse("theses:thesis", kwargs={"thesislink_id": thesis_link.id})
        response = client.post(target)
        self.assertEqual(response.status_code, 200)


class TestRequestThesisLink(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.client = Client()
        self.target = reverse("theses:request_thesislink")

    def test_response_when_not_logged_in(self):
        """
        A visitor that is not logged in cannot view this page and is redirected to login.
        """
        response = self.client.get(self.target)
        self.assertRedirects(
            response,
            expected_url="%s?next=%s"
            % (reverse("scipost:login"), reverse("theses:request_thesislink")),
        )

    def test_response_when_logged_in(self):
        request = RequestFactory().get(self.target)
        request.user = UserFactory()
        response = RequestThesisLink.as_view()(request)
        self.assertEqual(response.status_code, 200)


class TestVetThesisLinkRequests(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)
        self.client = Client()
        self.thesislink = ThesisLinkFactory()
        self.target = reverse(
            "theses:vet_thesislink", kwargs={"pk": self.thesislink.id}
        )

    def test_response_when_not_logged_in(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 403)

    def test_response_regular_contributor(self):
        """
        A Contributor needs to be in the Vetting Editors group to be able to
        vet submitted thesis links.
        """
        request = RequestFactory().get(self.target)
        user = UserFactory()
        request.user = user
        self.assertRaises(
            PermissionDenied, VetThesisLink.as_view(), request, pk=self.thesislink.id
        )

    def test_response_vetting_editor(self):
        request = RequestFactory().get(self.target)
        user = UserFactory()
        user.groups.add(Group.objects.get(name="Vetting Editors"))
        request.user = user
        response = VetThesisLink.as_view()(request, pk=self.thesislink.id)
        self.assertEqual(response.status_code, 200)

    # 2020-09-29 FAILS
    # def test_thesislink_is_vetted_by_correct_contributor_and_mail_is_sent(self):
    #     contributor = ContributorFactory()
    #     contributor.user.groups.add(Group.objects.get(name="Vetting Editors"))
    #     request = RequestFactory().get(self.target)
    #     request.user = contributor.user
    #     post_data = model_form_data(ThesisLinkFactory(), VetThesisLinkForm)
    #     post_data["action_option"] = VetThesisLinkForm.ACCEPT
    #     target = reverse('theses:vet_thesislink', kwargs={'pk': self.thesislink.id})

    #     print("post_data:\n\t%s" % post_data)
    #     request = RequestFactory().post(target, post_data)
    #     request.user = contributor.user

    #     # I don't know what the following three lines do, but they help make a RequestFactory
    #     # work with the messages middleware
    #     setattr(request, 'session', 'session')
    #     messages = FallbackStorage(request)
    #     setattr(request, '_messages', messages)

    #     response = VetThesisLink.as_view()(request, pk=self.thesislink.id)
    #     print("response:\n\t%s" % response)
    #     self.thesislink.refresh_from_db()
    #     self.assertEqual(self.thesislink.vetted_by, contributor)
    #     self.assertEqual(len(mail.outbox), 1)
    #     self.assertEqual(mail.outbox[0].subject, 'SciPost Thesis Link activated')

    # 2020-09-29 FAILS
    # def test_thesislink_that_is_refused_is_deleted_and_mail_is_sent(self):
    #     contributor = ContributorFactory()
    #     contributor.user.groups.add(Group.objects.get(name="Vetting Editors"))
    #     request = RequestFactory().get(self.target)
    #     request.user = contributor.user

    #     post_data = model_form_data(ThesisLinkFactory(), VetThesisLinkForm)
    #     post_data["action_option"] = VetThesisLinkForm.REFUSE
    #     post_data["refusal_reason"] = VetThesisLinkForm.ALREADY_EXISTS
    #     post_data["justification"] = "This thesis already exists."
    #     target = reverse('theses:vet_thesislink', kwargs={'pk': self.thesislink.id})

    #     request = RequestFactory().post(target, post_data)
    #     request.user = contributor.user

    #     # I don't know what the following three lines do, but they help make a RequestFactory
    #     # work with the messages middleware
    #     setattr(request, 'session', 'session')
    #     messages = FallbackStorage(request)
    #     setattr(request, '_messages', messages)

    #     response = VetThesisLink.as_view()(request, pk=self.thesislink.id)
    #     self.assertEqual(ThesisLink.objects.filter(id=self.thesislink.id).count(), 0)
    #     self.assertEqual(len(mail.outbox), 1)
    #     self.assertEqual(mail.outbox[0].subject, 'SciPost Thesis Link')

    # 2020-09-29 FAILS
    # def test_thesislink_is_vetted_by_correct_contributor_and_mail_is_sent_when_modified(self):
    #     contributor = ContributorFactory()
    #     contributor.user.groups.add(Group.objects.get(name="Vetting Editors"))
    #     request = RequestFactory().get(self.target)
    #     request.user = contributor.user
    #     post_data = model_form_data(ThesisLinkFactory(), VetThesisLinkForm)
    #     post_data["action_option"] = VetThesisLinkForm.MODIFY
    #     target = reverse('theses:vet_thesislink', kwargs={'pk': self.thesislink.id})

    #     request = RequestFactory().post(target, post_data)
    #     request.user = contributor.user

    #     # I don't know what the following three lines do, but they help make a RequestFactory
    #     # work with the messages middleware
    #     setattr(request, 'session', 'session')
    #     messages = FallbackStorage(request)
    #     setattr(request, '_messages', messages)

    #     response = VetThesisLink.as_view()(request, pk=self.thesislink.id)
    #     self.thesislink.refresh_from_db()
    #     self.assertEqual(self.thesislink.vetted_by, contributor)
    #     self.assertEqual(len(mail.outbox), 1)
    #     self.assertEqual(mail.outbox[0].subject, 'SciPost Thesis Link activated')


class TestTheses(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.client = Client()
        self.target = reverse("theses:theses")

    def test_empty_search_query(self):
        thesislink = ThesisLinkFactory()
        response = self.client.get(self.target)
        search_results = response.context["object_list"]
        self.assertTrue(thesislink in search_results)

    def test_search_query_on_author(self):
        thesislink = ThesisLinkFactory()
        other_thesislink = ThesisLinkFactory()
        form_data = {"author": thesislink.author}
        response = self.client.get(self.target, form_data)
        search_results = response.context["object_list"]
        self.assertTrue(thesislink in search_results)
        self.assertTrue(other_thesislink not in search_results)
        self.assertEqual(len(search_results), 1)
