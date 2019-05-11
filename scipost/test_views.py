__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.contrib.auth.models import Group
from django.test import TestCase, Client, tag

from commentaries.factories import UnvettedCommentaryFactory, CommentaryFactory,\
                                   UnpublishedCommentaryFactory
from commentaries.forms import CommentarySearchForm
from commentaries.models import Commentary

from .factories import ContributorFactory,\
                       EditorialCollegeFellowshipFactory, EditorialCollegeFactory
from .models import EditorialCollege, EditorialCollegeFellowship


class RequestCommentaryTest(TestCase):
    """Test cases for `request_commentary` view method"""
    fixtures = ['permissions', 'groups', 'contributors']

    def setUp(self):
        self.view_url = reverse('commentaries:request_commentary')
        self.login_url = reverse('scipost:login')
        self.redirected_login_url = '%s?next=%s' % (self.login_url, self.view_url)

    def test_get_requests(self):
        """Test different GET requests on view"""
        # Anoymous user should redirect to login page
        request = self.client.get(self.view_url)
        self.assertRedirects(request, self.redirected_login_url)

        # Registered Contributor should get 200
        self.client.login(username="Test", password="testpw")
        request = self.client.get(self.view_url)
        self.assertEquals(request.status_code, 200)

    def test_post_invalid_forms(self):
        """Test different kind of invalid RequestCommentaryForm submits"""
        self.client.login(username="Test", password="testpw")
        request = self.client.post(self.view_url)
        self.assertEquals(request.status_code, 200)


class VetCommentaryRequestsTest(TestCase):
    """Test cases for `vet_commentary_requests` view method"""
    fixtures = ['groups', 'permissions']

    def setUp(self):
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
        CommentaryFactory()
        response = self.client.get(self.view_url)
        self.assertEquals(response.context['commentary_to_vet'], None)

        # Unvetted Commentaries do exist!
        UnvettedCommentaryFactory()
        response = self.client.get(self.view_url)
        self.assertTrue(type(response.context['commentary_to_vet']) is Commentary)


class BrowseCommentariesTest(TestCase):
    """Test cases for `browse` view."""
    fixtures = ['groups', 'permissions']

    def setUp(self):
        CommentaryFactory(discipline='physics')
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
    fixtures = ['permissions', 'groups']

    def setUp(self):
        self.client = Client()
        self.commentary = UnpublishedCommentaryFactory()
        self.target = reverse(
            'commentaries:commentary',
            kwargs={'arxiv_or_DOI_string': self.commentary.arxiv_or_DOI_string}
        )

    def test_status_code_200(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)


@tag('static-info', 'full')
class AboutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.target = reverse('scipost:about')

        # Create College with 10 members
        self.college = EditorialCollegeFactory()
        EditorialCollegeFellowshipFactory.create_batch(10)

    def test_status_code_200_including_members(self):
        response = self.client.get(self.target)
        self.assertEqual(response.status_code, 200)

        # College exists in context
        self.assertTrue('object_list' in response.context)
        college = response.context['object_list'][0]
        self.assertTrue(isinstance(college, EditorialCollege))

        # Members exist in college
        self.assertTrue(college.member.count() >= 10)
        last_member = college.member.last()
        self.assertTrue(isinstance(last_member, EditorialCollegeFellowship))
