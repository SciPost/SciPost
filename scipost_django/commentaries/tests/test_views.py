__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.contrib.auth.models import Group
from django.test import TestCase, Client, RequestFactory

from scipost.models import Contributor
from scipost.factories import ContributorFactory, UserFactory

from ..factories import (
    UnvettedCommentaryFactory,
    CommentaryFactory,
    UnpublishedCommentaryFactory,
    UnvettedUnpublishedCommentaryFactory,
)
from ..forms import RequestPublishedArticleForm
from ..models import Commentary
from ..views import RequestPublishedArticle, prefill_using_DOI, RequestArxivPreprint
from common.helpers.test import add_groups_and_permissions
from common.helpers import model_form_data


class PrefillUsingDOITest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.target = reverse("commentaries:prefill_using_DOI")
        self.physrev_doi = "10.1103/PhysRevB.92.214427"

    def test_submit_valid_physrev_doi(self):
        post_data = {"doi": self.physrev_doi}
        request = RequestFactory().post(self.target, post_data)
        request.user = UserFactory()

        response = prefill_using_DOI(request)
        self.assertEqual(response.status_code, 200)


# NOTED AS FAILING 2019-11-06
# class RequestPublishedArticleTest(TestCase):
#     def setUp(self):
#         add_groups_and_permissions()
#         self.target = reverse('commentaries:request_published_article')
#         self.contributor = ContributorFactory()
#         self.commentary_instance = UnvettedCommentaryFactory.build(requested_by=self.contributor)
#         self.valid_form_data = model_form_data(self.commentary_instance, RequestPublishedArticleForm)

#     def test_commentary_gets_created_with_correct_type_and_link(self):
#         request = RequestFactory().post(self.target, self.valid_form_data)
#         request.user = self.contributor.user

#         self.assertEqual(Commentary.objects.count(), 0)
#         response = RequestPublishedArticle.as_view()(request)
#         self.assertEqual(Commentary.objects.count(), 1)

#         commentary = Commentary.objects.first()
#         self.assertEqual(commentary.pub_DOI, self.valid_form_data['pub_DOI'])
#         self.assertEqual(commentary.type, 'published')
#         self.assertEqual(commentary.arxiv_or_DOI_string, commentary.pub_DOI)
#         self.assertEqual(commentary.requested_by, self.contributor)


# NOTED AS FAILING 2019-11-06
# class RequestArxivPreprintTest(TestCase):
#     def setUp(self):
#         add_groups_and_permissions()
#         self.target = reverse('commentaries:request_arxiv_preprint')
#         self.contributor = ContributorFactory()
#         self.commentary_instance = UnvettedUnpublishedCommentaryFactory.build(
#             requested_by=self.contributor)
#         self.valid_form_data = model_form_data(self.commentary_instance, RequestPublishedArticleForm)
#         # The form field is called 'identifier', while the model field is called 'arxiv_identifier',
#         # so model_form_data doesn't include it.
#         self.valid_form_data['arxiv_identifier'] = self.commentary_instance.arxiv_identifier

# def test_commentary_gets_created_with_correct_type_and_link_and_requested_by(self):
#     request = RequestFactory().post(self.target, self.valid_form_data)
#     request.user = self.contributor.user

#     self.assertEqual(Commentary.objects.count(), 0)
#     response = RequestArxivPreprint.as_view()(request)
#     self.assertEqual(Commentary.objects.count(), 1)
#     commentary = Commentary.objects.first()
#     self.assertEqual(commentary.arxiv_identifier, self.valid_form_data['arxiv_identifier'])
#     self.assertEqual(commentary.type, 'preprint')
#     self.assertEqual(commentary.arxiv_or_DOI_string,
#                      "arXiv:" + self.commentary_instance.arxiv_identifier)
#     self.assertEqual(commentary.requested_by, self.contributor)


class VetCommentaryRequestsTest(TestCase):
    """Test cases for `vet_commentary_requests` view method"""

    def setUp(self):
        add_groups_and_permissions()
        self.view_url = reverse("commentaries:vet_commentary_requests")
        self.login_url = reverse("scipost:login")
        self.password = "test123"
        self.contributor = ContributorFactory(user__password=self.password)

    def set_required_permissions_and_login(self):
        """Set the required permissions to testuser to access vet_commentary_requests."""
        group = Group.objects.get(name="Vetting Editors")
        self.contributor.user.groups.add(group)
        self.client.login(
            username=self.contributor.user.username, password=self.password
        )

    def test_user_permissions(self):
        """Test view permission is restricted to Vetting Editors."""
        # Anoymous user
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 403)

        # Wrong permissions group
        self.client.login(
            username=self.contributor.user.username, password=self.password
        )
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 403)

        # Right permissions group
        self.set_required_permissions_and_login()
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)

    def test_get_valid_unvetted_commentaries(self):
        """Test if valid commentaries are sent back to user, if exists."""
        self.set_required_permissions_and_login()

        # No Commentary exists!
        response = self.client.get(self.view_url)
        self.assertTrue("commentary_to_vet" in response.context)
        self.assertEqual(response.context["commentary_to_vet"], None)

        # Only vetted Commentaries exist!
        # ContributorFactory.create_batch(5)
        CommentaryFactory(
            requested_by=ContributorFactory(), vetted_by=ContributorFactory()
        )
        response = self.client.get(self.view_url)
        self.assertEqual(response.context["commentary_to_vet"], None)

        # Unvetted Commentaries do exist!
        UnvettedCommentaryFactory(requested_by=ContributorFactory())
        response = self.client.get(self.view_url)
        self.assertTrue(type(response.context["commentary_to_vet"]) is Commentary)


class CommentaryDetailTest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.client = Client()
        self.commentary = UnpublishedCommentaryFactory(
            requested_by=ContributorFactory(), vetted_by=ContributorFactory()
        )
        self.target = reverse(
            "commentaries:commentary",
            kwargs={"arxiv_or_DOI_string": self.commentary.arxiv_or_DOI_string},
        )

    def test_status_code_200(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)

    def test_unvetted_commentary(self):
        commentary = UnvettedCommentaryFactory(requested_by=ContributorFactory())
        target = reverse(
            "commentaries:commentary",
            kwargs={"arxiv_or_DOI_string": commentary.arxiv_or_DOI_string},
        )
        response = self.client.get(target)
        self.assertEqual(response.status_code, 404)
