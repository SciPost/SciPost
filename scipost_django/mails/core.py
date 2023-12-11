__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from html2text import HTML2Text
import json
import re
import inspect

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import get_template

from common.utils import get_current_domain

from .exceptions import ConfigurationError


class MailEngine:
    """
    This engine processes the configuration and template files to be saved into the database in
    the MailLog table.
    """

    _required_parameters = ["recipient_list", "subject"]
    _possible_parameters = [
        "recipient_list",
        "subject",
        "from_email",
        "from_name",
        "bcc",
    ]
    _email_fields = ["recipient_list", "from_email", "bcc"]
    _processed_template = False
    _mail_sent = False

    def __init__(
        self,
        mail_code,
        subject="",
        recipient_list=[],
        bcc=[],
        from_email="",
        from_name="",
        **kwargs,
    ):
        """
        Start engine with specific mail_code. Any other keyword argument that is passed will
        be used as a variable in the mail template.

        @Arguments
        -- mail_code (str)

        @Keyword arguments
        The following arguments overwrite the default values, set in the configuration files:
        -- subject (str, optional)
        -- recipient_list (str, optional): List of email addresses or db-relations.
        -- bcc (str, optional): List of email addresses or db-relations.
        -- from_email (str, optional): Plain email address.
        -- from_name (str, optional): Display name for from address.
        """
        self.mail_code = mail_code
        self.extra_config = {
            "bcc": bcc,
            "subject": subject,
            "from_name": from_name,
            "from_email": from_email,
            "recipient_list": recipient_list,
        }
        self.template_variables = kwargs
        # Add the 'domain' template variable to all templates using the Sites framework:
        self.template_variables["domain"] = get_current_domain()

    def __repr__(self):
        return '<%(cls)s code="%(code)s", validated=%(validated)s sent=%(sent)s>' % {
            "cls": self.__class__.__name__,
            "code": self.mail_code,
            "validated": hasattr(self, "mail_data"),
            "sent": self._mail_sent,
        }

    def validate(self, render_template=False):
        """Check if MailEngine is valid and ready for sending."""
        self._read_configuration_file()
        self._detect_and_save_object()
        self._check_template_exists()
        self._validate_configuration()
        self._validate_email_fields()
        if render_template:
            self.render_template()

    def render_only(self):
        """Render template. To be used in mail backend only."""
        if not hasattr(self, "mail_data"):
            self.mail_data = {}
        self._check_template_exists()
        self.render_template()
        return self.mail_data["message"], self.mail_data.get("html_message", "")

    def render_template(self, html_message=None):
        """
        Render the template associated with the mail_code. If html_message is given,
        use this as a template instead.
        """
        if html_message:
            self.mail_data["html_message"] = html_message
        else:
            self.mail_data["html_message"] = self._template.render(
                self.template_variables
            )  # Damn slow.

        # Transform to non-HTML version.
        handler = HTML2Text()
        self.mail_data["message"] = handler.handle(self.mail_data["html_message"])
        self._processed_template = True

    def send_mail(self):
        """Send the mail."""
        if self._mail_sent:
            # Prevent double sending when using a Django form.
            return
        elif not hasattr(self, "mail_data"):
            raise ValueError(
                "The mail: %s could not be sent because the data didn't validate."
                % self.mail_code
            )
        email = EmailMultiAlternatives(
            self.mail_data["subject"],
            self.mail_data.get("message", ""),
            "%s <%s>"
            % (
                self.mail_data.get("from_name", "SciPost"),
                self.mail_data.get("from_email", "noreply@%s" % get_current_domain()),
            ),
            self.mail_data["recipient_list"],
            bcc=self.mail_data["bcc"],
            reply_to=[
                self.mail_data.get("from_email", "noreply@%s" % get_current_domain())
            ],
            headers={
                "delayed_processing": not self._processed_template,
                "context": self.template_variables,
                "mail_code": self.mail_code,
            },
        )

        # Send html version if available
        if "html_message" in self.mail_data:
            email.attach_alternative(self.mail_data["html_message"], "text/html")

        email.send(fail_silently=False)
        self._mail_sent = True

        if "object" in self.template_variables and hasattr(
            self.template_variables["object"], "mail_sent"
        ):
            self.template_variables["object"].mail_sent()

    def _detect_and_save_object(self):
        """
        Detect if less than or equal to one object exists and save it, else raise exception.
        Stick to Django's convention of saving it as a central `object` variable.
        """
        object = None
        context_object_name = None

        if "object" in self.template_variables:
            object = self.template_variables["object"]
            context_object_name = object._meta.model_name
        elif "instance" in self.template_variables:
            object = self.template_variables["instance"]
            context_object_name = object._meta.model_name
        else:
            for key, var in self.template_variables.items():
                if isinstance(var, models.Model):
                    if object:
                        raise ValueError(
                            "Multiple db instances are given. Please specify which object to use."
                        )
                    else:
                        object = var
        if object:
            self.template_variables["object"] = object

            if (
                context_object_name
                and context_object_name not in self.template_variables
            ):
                self.template_variables[context_object_name] = object

    def _read_configuration_file(self):
        """Retrieve default configuration for specific mail_code."""
        json_location = "%s/templates/email/%s.json" % (
            settings.BASE_DIR,
            self.mail_code,
        )

        try:
            with open(json_location, "r") as f:
                self.mail_data = json.loads(f.read())
        except OSError:
            raise ImportError(
                "No configuration file found. Mail code: %s" % self.mail_code
            )

        # Check if configuration file is valid.
        if "subject" not in self.mail_data:
            raise ConfigurationError('key "subject" is missing.')
        if "recipient_list" not in self.mail_data:
            raise ConfigurationError('key "recipient_list" is missing.')

        # Overwrite mail data if parameters are given.
        for key, val in self.extra_config.items():
            if val or key not in self.mail_data:
                self.mail_data[key] = val

    def _check_template_exists(self):
        """Save template or raise TemplateDoesNotExist."""
        self._template = get_template("email/%s.html" % self.mail_code)

    def _validate_configuration(self):
        """Check if all required data is given via either configuration or extra parameters."""

        # Check data is complete
        if not all(key in self.mail_data for key in self._required_parameters):
            txt = "Not all required parameters are given in the configuration file or on instantiation."
            txt += " Check required parameters: {}".format(self._required_parameters)
            raise ConfigurationError(txt)

        # Check if data is overcomplete/
        if not all(key in self._possible_parameters for key in self.mail_data.keys()):
            txt = "Configuration file may only contain the following parameters: {}.".format(
                self._possible_parameters
            )
            raise ConfigurationError(txt)

        # Check all configuration value types
        for email_key in ["subject", "from_email", "from_name"]:
            if email_key in self.mail_data and self.mail_data[email_key]:
                if not isinstance(self.mail_data[email_key], str):
                    raise ConfigurationError(
                        '"%(key)s" argument must be a string'
                        % {
                            "key": email_key,
                        }
                    )
        for email_key in ["recipient_list", "bcc"]:
            if email_key in self.mail_data and self.mail_data[email_key]:
                if not isinstance(self.mail_data[email_key], list):
                    raise ConfigurationError(
                        '"%(key)s" argument must be a list'
                        % {
                            "key": email_key,
                        }
                    )

    def _validate_email_fields(self):
        """Validate all email addresses in the mail config."""
        for email_key in self._email_fields:
            if emails := self.mail_data.get(email_key, None):
                emails = emails if isinstance(emails, list) else [emails]
                valid_emails = [
                    valid_entry
                    for entry in emails
                    if (valid_entry := self._validate_email_addresses(entry))
                ]

                if len(valid_emails) == 0:
                    raise ConfigurationError(
                        "No valid email addresses found for %s." % email_key
                    )

                if len(emails) == 1 and len(valid_emails) == 1:
                    valid_emails = valid_emails[0]

                self.mail_data[email_key] = valid_emails

    def _validate_email_addresses(self, entry):
        """
        Return email address given raw email, email prefix or database relation given in `entry`.
        """
        if re.match("[^@]+@[^@]+\.[^@]+", entry):
            # Email string
            return entry
        # if the email address is given as a prefix of the form `[recipient]@`, add domain name:
        elif re.match("[^@]+@$", entry):
            return "%s%s" % (entry, get_current_domain())
        elif self.template_variables["object"]:
            mail_to = self.template_variables["object"]
            for attr in entry.split("|")[0].split("."):
                try:
                    mail_to = getattr(mail_to, attr)
                    if inspect.ismethod(mail_to):
                        mail_to = mail_to()
                except AttributeError:
                    # Invalid property/mail
                    if entry.endswith("|None"):
                        # Allow None values
                        return None
                    raise KeyError("The property (%s) does not exist." % entry)
            return mail_to
        raise KeyError("Neither an email adress nor db instance is given.")
