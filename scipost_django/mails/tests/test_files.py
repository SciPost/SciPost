import glob
import os

from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase

from mails.core import MailEngine
from mails.exceptions import ConfigurationError


class MailLogFilesTests(TestCase):
    """
    Test if all defined templated emails are configured correctly.
    """

    def test_all_configuration_files(self):
        """Test configuration files found are valid."""
        folder = "templates/email"
        files = glob.glob("{}/**/*.json".format(folder), recursive=True)

        i = 0
        for path_file in files:
            file_name = path_file.replace(folder + "/", "")
            mail_code = os.path.splitext(file_name)[0]
            if mail_code.startswith("test"):
                # Skip all test files
                continue
            try:
                engine = MailEngine(mail_code)
                engine._read_configuration_file()
                engine._detect_and_save_object()
                engine._check_template_exists()
                engine._validate_configuration()
            except Exception as e:
                self.fail('Mail ("{}") configuration invalid:\n{}'.format(mail_code, e))
            i += 1
        print("Tested {} files".format(i))
