from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.test import TestCase, Client, RequestFactory

from scipost.factories import ContributorFactory, UserFactory

from .factories import UnvettedCommentaryFactory, VettedCommentaryFactory, UnpublishedVettedCommentaryFactory, \
    UnvettedArxivPreprintCommentaryFactory
from .forms import CommentarySearchForm, RequestPublishedArticleForm
from .models import Commentary
from .views import RequestPublishedArticle, prefill_using_DOI, RequestArxivPreprint
from common.helpers.test import add_groups_and_permissions
from common.helpers import model_form_data


class RequestCommentaryTest(TestCase):
    """Test cases for `request_commentary` view method"""
    def setUp(self):
        add_groups_and_permissions()
        self.view_url = reverse('commentaries:request_commentary')
        self.login_url = reverse('scipost:login')
        self.redirected_login_url = '%s?next=%s' % (self.login_url, self.view_url)

    def test_redirects_if_not_logged_in(self):
        request = self.client.get(self.view_url)
        self.assertRedirects(request, self.redirected_login_url)

    def test_valid_response_if_logged_in(self):
        """Test different GET requests on view"""
        request = RequestFactory().get(self.view_url)
        request.user = UserFactory()
        response = RequestCommentary.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post_invalid_forms(self):
        """Test different kind of invalid RequestCommentaryForm submits"""
        raise NotImplementedError

    def test_saved_commentary_has_a_type(self):
        self.assertEqual(Commentary.objects.count(), 0)
        commentary = UnvettedCommentaryFactory.build()
        valid_post_data = model_form_data(commentary, RequestPublishedArticleForm)
        print(valid_post_data)
        request = RequestFactory().post(reverse('commentaries:request_published_article'), valid_post_data)
        request.user = UserFactory()
        response = RequestPublishedArticle.as_view()(request)

        self.assertEqual(Commentary.objects.count(), 1)


class PrefillUsingDOITest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.target = reverse('commentaries:prefill_using_DOI')
        self.physrev_doi = '10.1103/PhysRevB.92.214427'

    def test_submit_valid_physrev_doi(self):
        post_data = {'doi': self.physrev_doi}
        request = RequestFactory().post(self.target, post_data)
        request.user = UserFactory()

        response = prefill_using_DOI(request)
        self.assertEqual(response.status_code, 200)


class RequestPublishedArticleTest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.target = reverse('commentaries:request_published_article')
        self.commentary_instance = UnvettedCommentaryFactory.build()
        self.valid_form_data = model_form_data(self.commentary_instance, RequestPublishedArticleForm)

    def test_commentary_gets_created(self):
        request = RequestFactory().post(self.target, self.valid_form_data)
        request.user = UserFactory()

        self.assertEqual(Commentary.objects.count(), 0)
        response = RequestPublishedArticle.as_view()(request)
        self.assertEqual(Commentary.objects.count(), 1)
        self.assertEqual(Commentary.objects.first().pub_DOI, self.valid_form_data['pub_DOI'])


class RequestArxivPreprintTest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.target = reverse('commentaries:request_arxiv_preprint')
        self.commentary_instance = UnvettedArxivPreprintCommentaryFactory.build()
        self.valid_form_data = model_form_data(self.commentary_instance, RequestPublishedArticleForm)
        # The form field is called 'identifier', while the model field is called 'arxiv_identifier',
        # so model_form_data doesn't include it.
        self.valid_form_data['arxiv_identifier'] = self.commentary_instance.arxiv_identifier

    def test_commentary_gets_created(self):
        request = RequestFactory().post(self.target, self.valid_form_data)
        request.user = UserFactory()

        self.assertEqual(Commentary.objects.count(), 0)
        response = RequestArxivPreprint.as_view()(request)
        self.assertEqual(Commentary.objects.count(), 1)
        self.assertEqual(Commentary.objects.first().arxiv_identifier, self.valid_form_data['arxiv_identifier'])

class VetCommentaryRequestsTest(TestCase):
    """Test cases for `vet_commentary_requests` view method"""

    def setUp(self):
        add_groups_and_permissions()
        self.view_url = reverse('commentaries:vet_commentary_requests')
        self.login_url = reverse('scipost:login')
        self.password = 'test123'
        self.contributor = ContributorFactory(user__password=self.password)

    def set_required_permissions_and_login(self):
        '''Set the required permissions to testuser to access vet_commentary_requests.'''
        group = Group.objects.get(name="Vetting Editors")
        self.contributor.user.groups.add(group)
        self.client.login(username=self.contributor.user.username, password=self.password)

    def test_user_permissions(self):
        """Test view permission is restricted to Vetting Editors."""
        # Anoymous user
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 403)

        # Wrong permissions group
        self.client.login(username=self.contributor.user.username, password=self.password)
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 403)

        # Right permissions group
        self.set_required_permissions_and_login()
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 200)

    def test_get_valid_unvetted_commentaries(self):
        """Test if valid commentaries are sent back to user, if exists."""
        self.set_required_permissions_and_login()

        # No Commentary exists!
        response = self.client.get(self.view_url)
        self.assertTrue('commentary_to_vet' in response.context)
        self.assertEquals(response.context['commentary_to_vet'], None)

        # Only vetted Commentaries exist!
        VettedCommentaryFactory()
        response = self.client.get(self.view_url)
        self.assertEquals(response.context['commentary_to_vet'], None)

        # Unvetted Commentaries do exist!
        UnvettedCommentaryFactory()
        response = self.client.get(self.view_url)
        self.assertTrue(type(response.context['commentary_to_vet']) is Commentary)


class BrowseCommentariesTest(TestCase):
    """Test cases for `browse` view."""

    def setUp(self):
        add_groups_and_permissions()
        VettedCommentaryFactory(discipline='physics')
        self.view_url = reverse('commentaries:browse', kwargs={
            'discipline': 'physics',
            'nrweeksback': '1'
            })

    def test_response_list(self):
        '''Test if the browse view is passing commentaries to anoymous users.'''
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 200)

        # The created vetted Commentary is found!
        self.assertTrue(response.context['commentary_browse_list'].count() >= 1)
        # The search form is passed trough the view...
        self.assertTrue(type(response.context['form']) is CommentarySearchForm)


class CommentaryDetailTest(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        self.client = Client()
        self.commentary = UnpublishedVettedCommentaryFactory()
        self.target = reverse(
            'commentaries:commentary',
            kwargs={'arxiv_or_DOI_string': self.commentary.arxiv_or_DOI_string}
        )

    def test_status_code_200(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)
