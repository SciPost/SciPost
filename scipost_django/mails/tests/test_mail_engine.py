from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase

from mails.core import MailEngine
from mails.exceptions import ConfigurationError


class MailLogModelTests(TestCase):
    """
    Test the MailEngine object.
    """

    def test_valid_instantiation(self):
        """Test if init method of the engine works properly."""
        # Test no mail_code given fails.
        with self.assertRaises(TypeError):
            MailEngine()

        # Test only mail_code given works.
        try:
            MailEngine("tests/test_mail_code_1")
        except:
            # For whatever reason possible...
            self.fail("MailEngine() raised unexpectedly!")

        # Test all extra arguments are accepted.
        try:
            MailEngine(
                "tests/test_mail_code_1",
                subject="Test subject A",
                recipient_list=["test_A@example.org", "test_B@example.org"],
                bcc=["test_C@example.com", "test_D@example.com"],
                from_email="test@example.org",
                from_name="John Doe",
            )
        except KeyError:
            self.fail("MailEngine() does not accept all keyword arguments!")

        # Test if only proper arguments are accepted.
        with self.assertRaises(ConfigurationError):
            engine = MailEngine(
                "tests/test_mail_code_1", recipient_list="test_A@example.org"
            )
            engine.validate()
        with self.assertRaises(ConfigurationError):
            engine = MailEngine("tests/test_mail_code_1", bcc="test_A@example.org")
            engine.validate()
        with self.assertRaises(ConfigurationError):
            engine = MailEngine(
                "tests/test_mail_code_1", from_email=["test_A@example.org"]
            )
            engine.validate()

        # See if any other keyword argument is accepted and saved as template variable.
        try:
            engine = MailEngine(
                "tests/test_mail_code_1",
                fake="Test subject A",
                extra=["test_A@example.org"],
            )
        except KeyError:
            self.fail("MailEngine() does not accept extra keyword arguments!")

        self.assertIs(engine.template_variables["fake"], "Test subject A")
        self.assertListEqual(engine.template_variables["extra"], ["test_A@example.org"])

    def test_invalid_mail_code(self):
        """Test if invalid configuration files are handled properly."""
        with self.assertRaises(ImportError):
            engine = MailEngine("tests/fake_mail_code_1")
            engine.validate()
        with self.assertRaises(ConfigurationError):
            engine = MailEngine("tests/test_mail_code_fault_1")
            engine.validate()
        with self.assertRaises(TemplateDoesNotExist):
            engine = MailEngine("tests/test_mail_code_no_template_1")
            engine.validate()

    def test_positive_validation_delayed_rendering(self):
        """Test if validation works and rendering is delayed."""
        engine = MailEngine("tests/test_mail_code_1")
        engine.validate()  # Should validate without rendering
        self.assertIn("subject", engine.mail_data)
        self.assertIn("recipient_list", engine.mail_data)
        self.assertIn("from_email", engine.mail_data)
        self.assertNotIn("message", engine.mail_data)
        self.assertNotIn("html_message", engine.mail_data)
        self.assertEqual(engine.mail_data["subject"], "SciPost Test")
        self.assertIn("test@scipost.org", engine.mail_data["recipient_list"])
        self.assertEqual(engine.mail_data["from_email"], "admin@scipost.org")

    def test_positive_direct_validation(self):
        """Test if validation and rendering works as required."""
        engine = MailEngine("tests/test_mail_code_1")
        engine.validate(render_template=True)  # Should validate and render
        self.assertIn("message", engine.mail_data)
        self.assertIn("html_message", engine.mail_data)
        self.assertNotEqual(engine.mail_data["message"], "")
        self.assertNotEqual(engine.mail_data["html_message"], "")

    def test_additional_parameters(self):
        """Test if validation and rendering works as required if given extra parameters."""
        engine = MailEngine(
            "tests/test_mail_code_1",
            subject="Test Subject 2",
            recipient_list=["test1@scipost.org"],
            bcc=["test2@scipost.org"],
            from_email="test3@scipost.org",
            from_name="Test Name",
            weird_variable_name="John Doe",
        )
        engine.validate()
        self.assertEqual(engine.mail_data["subject"], "Test Subject 2")
        self.assertIn("test1@scipost.org", engine.mail_data["recipient_list"])
        self.assertIn("test2@scipost.org", engine.mail_data["bcc"])
        self.assertEqual(engine.mail_data["from_email"], "test3@scipost.org")
        self.assertEqual(engine.mail_data["from_name"], "Test Name")
        self.assertNotIn("weird_variable_name", engine.mail_data)
        self.assertIn("weird_variable_name", engine.template_variables)
        self.assertEqual(engine.template_variables["weird_variable_name"], "John Doe")
