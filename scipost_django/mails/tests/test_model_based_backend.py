from contextlib import redirect_stdout
from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from mails.models import MailLog, MAIL_RENDERED, MAIL_NOT_RENDERED, MAIL_SENT
from mails.utils import DirectMailUtil
from submissions.factories import SubmissionFactory


class ModelEmailBackendTests(TestCase):
    """
    Test the ModelEmailBackend object assuming the MailEngine and DirectMailUtil work properly.
    """

    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def test_non_rendered_database_entries(self):
        """Test non rendered mail database entries are correct after sending email."""
        with self.settings(EMAIL_BACKEND="mails.backends.filebased.ModelEmailBackend"):
            mail_util = DirectMailUtil(
                "tests/test_mail_code_1",
                subject="Test Subject Unique For Testing 93872",
                recipient_list=["test1@scipost.org"],
                cc=["testcc@scipost.org"],
                bcc=["test2@scipost.org"],
                from_email="test3@scipost.org",
                from_name="Test Name",
                weird_variable_name="John Doe",
            )
            self.assertFalse(mail_util.engine._mail_sent)
            mail_util.send_mail()
            self.assertTrue(mail_util.engine._mail_sent)

        mail_log = MailLog.objects.last()
        self.assertFalse(mail_log.processed)
        self.assertEqual(mail_log.status, MAIL_NOT_RENDERED)
        self.assertEqual(mail_log.mail_code, "tests/test_mail_code_1")
        self.assertEqual(mail_log.subject, "Test Subject Unique For Testing 93872")
        self.assertEqual(mail_log.body, "")
        self.assertEqual(mail_log.body_html, "")
        self.assertIn("test1@scipost.org", mail_log.to_recipients)
        self.assertIn("testcc@scipost.org", mail_log.cc_recipients)
        self.assertIn("test2@scipost.org", mail_log.bcc_recipients)
        self.assertEqual("Test Name <test3@scipost.org>", mail_log.from_email)

    def test_rendered_database_entries(self):
        """Test rendered mail database entries are correct after sending email."""
        with self.settings(EMAIL_BACKEND="mails.backends.filebased.ModelEmailBackend"):
            mail_util = DirectMailUtil(
                "tests/test_mail_code_1",
                delayed_processing=False,
                subject="Test Subject Unique For Testing 786234",
            )  # Use weird subject to confirm right instance.
            mail_util.send_mail()

        mail_log = MailLog.objects.last()
        self.assertEqual(mail_log.status, MAIL_RENDERED)
        self.assertEqual(mail_log.subject, "Test Subject Unique For Testing 786234")
        self.assertNotEqual(mail_log.body, "")
        self.assertNotEqual(mail_log.body_html, "")

    def test_context_saved_to_database(self):
        """Test mail database entries have relations with their context items."""
        with self.settings(EMAIL_BACKEND="mails.backends.filebased.ModelEmailBackend"):
            mail_util = DirectMailUtil(
                "tests/test_mail_code_1",
                subject="Test Subject Unique For Testing 786234",
                weird_variable_name="TestValue1",
                random_submission_relation=self.submission,
            )
            mail_util.send_mail()

        mail_log = MailLog.objects.last()
        context = mail_log.get_full_context()
        self.assertEqual(mail_log.status, MAIL_NOT_RENDERED)
        self.assertEqual(mail_log.subject, "Test Subject Unique For Testing 786234")
        self.assertIn("random_submission_relation", context)
        self.assertEqual(context["random_submission_relation"], self.submission)
        self.assertIn("weird_variable_name", context)
        self.assertEqual(context["weird_variable_name"], "TestValue1")

    def test_management_command(self):
        """Test if management command does the updating of the mail."""
        with self.settings(EMAIL_BACKEND="mails.backends.filebased.ModelEmailBackend"):
            mail_util = DirectMailUtil("tests/test_mail_code_1", object=self.submission)
            mail_util.send_mail()

        mail_log = MailLog.objects.last()

        # Capture stdout to check for command output.
        stdout = StringIO()
        with redirect_stdout(stdout):
            call_command("send_mails", id=mail_log.id)

        self.assertIn("Sent 1 mails.", stdout.getvalue())

        mail_log.refresh_from_db()
        self.assertNotEqual(mail_log.body, "")
        self.assertNotEqual(mail_log.body_html, "")
        self.assertEqual(mail_log.status, MAIL_SENT)
