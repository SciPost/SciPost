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
        with self.settings(EMAIL_BACKEND='mails.backends.filebased.ModelEmailBackend'):
            mail_util = DirectMailUtil(
                'tests/test_mail_code_1',
                subject='Test Subject Unique For Testing 93872',
                recipient_list=['test1@scipost.org'],
                bcc=['test2@scipost.org'],
                from_email='test3@scipost.org',
                from_name='Test Name',
                weird_variable_name='John Doe')
            self.assertFalse(mail_util.engine._mail_sent)
            mail_util.send_mail()
            self.assertTrue(mail_util.engine._mail_sent)

        mail = MailLog.objects.last()
        self.assertFalse(mail.processed)
        self.assertEqual(mail.status, MAIL_NOT_RENDERED)
        self.assertEqual(mail.mail_code, 'tests/test_mail_code_1')
        self.assertEqual(mail.subject, 'Test Subject Unique For Testing 93872')
        self.assertEqual(mail.body, '')
        self.assertEqual(mail.body_html, '')
        self.assertIn('test1@scipost.org', mail.to_recipients)
        self.assertIn('test2@scipost.org', mail.bcc_recipients)
        self.assertEqual('Test Name <test3@scipost.org>', mail.from_email)

    def test_rendered_database_entries(self):
        """Test rendered mail database entries are correct after sending email."""
        with self.settings(EMAIL_BACKEND='mails.backends.filebased.ModelEmailBackend'):
            mail_util = DirectMailUtil(
                'tests/test_mail_code_1',
                delayed_processing=False,
                subject='Test Subject Unique For Testing 786234')  # Use weird subject to confirm right instance.
            mail_util.send_mail()

        mail = MailLog.objects.last()
        self.assertEqual(mail.status, MAIL_RENDERED)
        self.assertEqual(mail.subject, 'Test Subject Unique For Testing 786234')
        self.assertNotEqual(mail.body, '')
        self.assertNotEqual(mail.body_html, '')

    def test_context_saved_to_database(self):
        """Test mail database entries have relations with their context items."""
        with self.settings(EMAIL_BACKEND='mails.backends.filebased.ModelEmailBackend'):
            mail_util = DirectMailUtil(
                'tests/test_mail_code_1',
                subject='Test Subject Unique For Testing 786234',
                weird_variable_name='TestValue1',
                random_submission_relation=self.submission)
            mail_util.send_mail()

        mail = MailLog.objects.last()
        context = mail.get_full_context()
        self.assertEqual(mail.status, MAIL_NOT_RENDERED)
        self.assertEqual(mail.subject, 'Test Subject Unique For Testing 786234')
        self.assertIn('random_submission_relation', context)
        self.assertEqual(context['random_submission_relation'], self.submission)
        self.assertIn('weird_variable_name', context)
        self.assertEqual(context['weird_variable_name'], 'TestValue1')

    def test_management_command(self):
        """Test if management command does the updating of the mail."""
        with self.settings(EMAIL_BACKEND='mails.backends.filebased.ModelEmailBackend'):
            mail_util = DirectMailUtil('tests/test_mail_code_1', object=self.submission)
            mail_util.send_mail()

        mail = MailLog.objects.last()
        call_command('send_mails', id=mail.id)

        mail.refresh_from_db()
        self.assertNotEqual(mail.body, '')
        self.assertNotEqual(mail.body_html, '')
        self.assertEqual(mail.status, MAIL_SENT)
