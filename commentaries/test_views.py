from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase

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
