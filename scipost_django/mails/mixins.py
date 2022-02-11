__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import time
import re
import json
import inspect
from html2text import HTML2Text

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.conf import settings
from django.template import loader

from scipost.models import Contributor


class MailUtilsMixin:
    """
    This mixin takes care of inserting the default data into the Utils or Form.

    DEPRECATED
    """

    instance = None
    mail_data = {}
    mail_template = ""
    html_message = ""
    message = ""
    original_recipient = ""
    mail_sent = False
    delayed_processing = False

    def __init__(self, *args, **kwargs):
        """Init an instance for a specific mail_code.

        Arguments:
        -- mail_code (str)
        -- subject (str)
        -- to (str): Email address or relation on the `instance`. Separated by comma.
        -- bcc_to (str, optional): Email address or relation on the `instance`. Separated by comma.
        -- instance: Instance of central object in email.
        -- from (str, optional): Plain email address.
        -- from_name (str, optional): Display name for from address.
        """
        self.pre_validation(*args, **kwargs)
        super().__init__(*args)

    def pre_validation(self, *args, **kwargs):
        """Validate the incoming data to initiate a specific mail."""
        self.mail_code = kwargs.pop("mail_code")
        self.instance = kwargs.pop("instance", None)
        kwargs["object"] = self.instance  # Similar template nomenclature as Django.
        self.mail_data = {
            "subject": kwargs.pop("subject", ""),
            "to_address": kwargs.pop("to", ""),
            "bcc_to": kwargs.pop("bcc", ""),
            "from_address_name": kwargs.pop("from_name", "SciPost"),
            "from_address": kwargs.pop(
                "from", "no-reply@%s" % Site.objects.get_current().domain
            ),
        }

        # Gather meta data
        json_location = "%s/templates/email/%s.json" % (
            settings.BASE_DIR,
            self.mail_code,
        )

        try:
            self.mail_data.update(json.loads(open(json_location).read()))
        except OSError:
            if not self.mail_data["subject"]:
                raise NotImplementedError(
                    (
                        "You did not create a valid .html and .json file "
                        "for mail_code: %s" % self.mail_code
                    )
                )

        # Save central object/instance if not already
        self.instance = self.get_object(**kwargs)

        # Digest the templates
        if not self.delayed_processing:
            mail_template = loader.get_template("email/%s.html" % self.mail_code)
            if self.instance and self.mail_data.get("context_object"):
                kwargs[self.mail_data["context_object"]] = self.instance
            self.mail_template = mail_template.render(kwargs)  # Damn slow.

        # Gather Recipients data
        try:
            self.original_recipient = self._validate_single_entry(
                self.mail_data.get("to_address")
            )[0]
        except IndexError:
            self.original_recipient = ""

        self.subject = self.mail_data["subject"]

    def get_object(self, **kwargs):
        if self.instance:
            return self.instance

        if self.mail_data.get("context_object"):
            return kwargs.get(self.mail_data["context_object"], None)

    def _validate_single_entry(self, entry):
        """
        entry -- raw email string or path or properties leading to email mail field

        Returns a list of email addresses found.
        """
        if entry and self.instance:
            if re.match("[^@]+@[^@]+\.[^@]+", entry):
                # Email string
                return [entry]
            else:
                mail_to = self.instance
                for attr in entry.split("."):
                    try:
                        mail_to = getattr(mail_to, attr)
                        if inspect.ismethod(mail_to):
                            mail_to = mail_to()
                    except AttributeError:
                        # Invalid property/mail
                        return []

                if not isinstance(mail_to, list):
                    return [mail_to]
                else:
                    return mail_to
        elif re.match("[^@]+@[^@]+\.[^@]+", entry):
            return [entry]
        else:
            return []

    def validate_bcc_list(self):
        """
        bcc_to in the .json file may contain multiple raw email addreses or property paths to
        an email field. The different entries need to be comma separated.
        """
        # Get recipients list. Try to send through BCC to prevent privacy issues!
        self.bcc_list = []
        if self.mail_data.get("bcc_to"):
            for bcc_entry in self.mail_data["bcc_to"].split(","):
                self.bcc_list += self._validate_single_entry(bcc_entry)

    def validate_recipients(self):
        # Check the send list
        if isinstance(self.original_recipient, list):
            recipients = self.original_recipient
        elif not isinstance(self.original_recipient, str):
            try:
                recipients = list(self.original_recipient)
            except TypeError:
                recipients = [self.original_recipient]
        else:
            recipients = [self.original_recipient]
        recipients = list(recipients)

        # Check if email needs to be taken from an instance
        _recipients = []
        for recipient in recipients:
            if isinstance(recipient, Contributor):
                _recipients.append(recipient.user.email)
            elif isinstance(recipient, get_user_model()):
                _recipients.append(recipient.email)
            elif isinstance(recipient, str):
                _recipients.append(recipient)
        self.recipients = _recipients

    def validate_message(self):
        if not self.html_message:
            self.html_message = self.mail_template
        handler = HTML2Text()
        self.message = handler.handle(self.html_message)

    def validate(self):
        """Execute different validation methods.

        Only to be used when the default data is used, eg. not in the EmailTemplateForm.
        """
        self.validate_message()
        self.validate_bcc_list()
        self.validate_recipients()
        self.save_mail_data()

    def save_mail_data(self):
        """Save mail validated mail data; update default values of mail data."""
        self.mail_data.update(
            {
                "subject": self.subject,
                "message": self.message,
                "html_message": self.html_message,
                "recipients": self.recipients,
                "bcc_list": self.bcc_list,
            }
        )

    def set_alternative_sender(self, from_name, from_address):
        """TODO: REMOVE; DEPRECATED

        Set an alternative from address/name from the default values received from the json
        config file. The arguments only take raw string data, no methods/properties!
        """
        self.mail_data["from_address_name"] = from_name
        self.mail_data["from_address"] = from_address

    def send(self):
        """Send the mail assuming `mail_data` is validated and complete."""
        if self.mail_sent:
            # Prevent double sending when using a Django form.
            return

        email = EmailMultiAlternatives(
            self.mail_data["subject"],
            self.mail_data["message"],
            "%s <%s>"
            % (self.mail_data["from_address_name"], self.mail_data["from_address"]),
            self.mail_data["recipients"],
            bcc=self.mail_data["bcc_list"],
            reply_to=[self.mail_data["from_address"]],
            headers={
                "delayed_processing": self.delayed_processing,
                "content_object": self.get_object(),
                "mail_code": self.mail_code,
            },
        )

        # Send html version if available
        if "html_message" in self.mail_data:
            email.attach_alternative(self.mail_data["html_message"], "text/html")

        email.send(fail_silently=False)
        self.mail_sent = True

        if self.instance and hasattr(self.instance, "mail_sent"):
            self.instance.mail_sent()
