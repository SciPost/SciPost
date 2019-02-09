from django.test import TestCase

from mails.core import MailEngine


class MailLogModelTests(TestCase):
    """
    Test the MailEngine object.
    """
    # def setUp(self):
    #     pass

    def test_valid_initialisation(self):
        """Test if the initialisation of the engine works properly."""
        # Test no mail_code given fails.
        with self.assertRaises(TypeError):
            MailEngine()

        # Test only mail_code given works.
        try:
            MailEngine('test_mail_code_1')
        except:
            # For whatever reason possible...
            self.fail('MailEngine() raised unexpectedly!')

        # Test all extra arguments are accepted.
        try:
            MailEngine(
                'test_mail_code_1',
                subject='Test subject A',
                recipient_list=['test_A@example.org', 'test_B@example.org'],
                bcc=['test_C@example.com', 'test_D@example.com'],
                from_email='test@example.org',
                from_name='John Doe')
        except KeyError:
            self.fail('MailEngine() does not accept all keyword arguments!')

        # Test if only proper arguments are accepted.
        with self.assertRaises(TypeError):
            MailEngine('test_mail_code_1', recipient_list='test_A@example.org')
        with self.assertRaises(TypeError):
            MailEngine('test_mail_code_1', bcc='test_A@example.org')
        with self.assertRaises(TypeError):
            MailEngine('test_mail_code_1', from_email=['test_A@example.org'])

        # See if any other keyword argument is accepted and saved as template variable.
        try:
            engine = MailEngine(
                'test_mail_code_1',
                fake='Test subject A',
                extra=['test_A@example.org'])
        except KeyError:
            self.fail('MailEngine() does not accept extra keyword arguments!')
        self.assertIs(engine.template_variables['fake'], 'Test subject A')
        self.assertListEqual(engine.template_variables['extra'], ['test_A@example.org'])
