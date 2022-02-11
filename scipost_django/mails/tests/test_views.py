from django.test import TestCase

# from mails.models import MailLog, MAIL_RENDERED, MAIL_NOT_RENDERED, MAIL_SENT
# from mails.utils import DirectMailUtil
from mails.views import MailView, MailEditorSubview

# from submissions.factories import SubmissionFactory


class MailDetailViewTest(TestCase):
    """
    Test the mails.views.MailView CBV.
    """

    def test_properly_functioning(self):
        """Test if CBV works properly as decribed in readme, with and without extra form."""
        pass

    def test_fails_properly(self):
        """Test if CBV fails gently if not used properly."""
        pass


class MailEditorSubviewTest(TestCase):
    """
    Test the mails.views.MailEditorSubview FBV.
    """

    def test_properly_functioning(self):
        """Test if CBV works properly as decribed in readme, with and without extra form."""
        pass

    def test_fails_properly(self):
        """Test if CBV fails gently if not used properly."""
        pass
