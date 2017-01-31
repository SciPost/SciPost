from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.test import TestCase

from scipost.factories import ContributorFactory

from .factories import UnVettedCommentaryFactory


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
        self.contributor = ContributorFactory()

    def test_not_logged_in_user(self):
        """Test view permission is restricted to logged in users."""
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 403)

    def test_get_valid_http_responses(self):
        """Test http response on GET requests"""
        # Registered Contributor should get 200
        self.client.login(username=self.contributor.user.username,
                          password='adm1n')

        # Wrong permissions group!
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 403)

        # Right permissions group!
        group = Group.objects.get(name="Vetting Editors")
        self.contributor.user.groups.add(group)
        response = self.client.get(self.view_url)
        self.assertEquals(response.status_code, 200)

    # def test_get_valid_unvetted_commentaries(self):
    #     """Test if valid commentaries are sent back to user."""
    #     self.client.login(username="Test", password="testpw")
    #     request = self.client.get(self.view_url)
    #     print(request)
