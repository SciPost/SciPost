__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.urls import reverse
from django.test import TestCase, Client

from mock import Mock, patch

from scipost.factories import UserFactory, TOTPDeviceFactory
from scipost.totp import TOTPVerification

# Mock random test time of which the test values are know
# Secret key: 'XTNHYG5OJPQ7ZRDC'
# Valid token: '451977'
mock_time = Mock()
mock_time.return_value = datetime.datetime(2019, 12, 8, 11, 1, 1).timestamp()


class TOTPVerificationTest(TestCase):
    """
    Test the scipost.totp.TOTPVerification util.
    """

    valid_secret_key = "XTNHYG5OJPQ7ZRDC"
    valid_token = "451977"

    def setUp(self):
        super().setUp()
        self.client = Client()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.password = "super_secret_123"
        cls.user = UserFactory(contrib=None)
        cls.user.set_password(cls.password)
        cls.user.save()

    @patch("time.time", mock_time)
    def test_proper_return_classmethod(self):
        """Test if valid secret_key/time/token combinations return True."""
        self.assertTrue(
            TOTPVerification.verify_token(self.valid_secret_key, self.valid_token)
        )
        self.assertFalse(
            TOTPVerification.verify_token("XTNHYG5OJPQ7ZRDX", self.valid_token)
        )
        self.assertFalse(
            TOTPVerification.verify_token(self.valid_secret_key, "4519000")
        )

    def test_2fa_workaround_closed(self):
        """
        Test if the admin login form is disabled. It's an easy workaround for 2FA.
        """
        # Test GET request
        self.client.logout()
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 301)  # Disabled by permanent redirect

        # Test POST request
        response = self.client.post(
            "/admin",
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
            },
        )
        self.assertNotEqual(response.context["user"], self.user)
        self.assertEqual(response.redirect_chain[0][0], "/admin/")
        self.assertEqual(
            response.redirect_chain[0][1], 301
        )  # Check if immediately redirected

    @patch("time.time", mock_time)
    def test_proper_login_procedure(self):
        """Test if CBV fails gently if not used properly."""

        login_url = reverse("scipost:login")
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)

        # Does posting work?
        response = self.client.post(
            login_url,
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
                "code": "",
            },
        )
        self.assertEqual(response.context["user"], self.user)
        self.assertEqual(
            response.redirect_chain[-1][0], "/"
        )  # Check if eventually redirected
        self.assertEqual(response.redirect_chain[-1][1], 302)

        # Logout for next step
        self.client.logout()

        # Check if a simple login without code fails if device is set up.
        TOTPDeviceFactory.create(user=self.user, token=self.valid_secret_key)
        response = self.client.post(
            login_url,
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
                "code": "",
            },
        )
        self.assertNotEqual(response.context["user"], self.user)

        # Check if login fails with invalid code
        response = self.client.post(
            login_url,
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
                "code": "912334",
            },
        )
        self.assertNotEqual(response.context["user"], self.user)
        response = self.client.post(
            login_url,
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
                "code": "000000",
            },
        )
        self.assertNotEqual(response.context["user"], self.user)

        # Check if login *WORKS* with a valid code.
        response = self.client.post(
            login_url,
            follow=True,
            data={
                "username": self.user.username,
                "password": self.password,
                "next": "/",
                "code": self.valid_token,
            },
        )
        self.assertEqual(response.context["user"], self.user)
