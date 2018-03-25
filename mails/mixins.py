__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
import json
import inspect
from html2text import HTML2Text

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template import loader

from scipost.models import Contributor


class MailUtilsMixin:
    """
    This mixin takes care of inserting the default data into the Utils or Form.
    """
    object = None
    mail_fields = {}
    mail_template = ''
    html_message = ''
    message = ''
    original_recipient = ''

    def __init__(self, *args, **kwargs):
        self.pre_validation(*args, **kwargs)
        super().__init__(*args)

    def pre_validation(self, *args, **kwargs):
        """
        This method should be called when initiating the object.
        """
        self.mail_code = kwargs.pop('mail_code')
        self.instance = kwargs.pop('instance', None)

        # Gather meta data
        json_location = '%s/mails/templates/mail_templates/%s.json' % (settings.BASE_DIR,
                                                                       self.mail_code)
        try:
            self.mail_data = json.loads(open(json_location).read())
        except OSError:
            raise NotImplementedError(('You did not create a valid .html and .json file '
                                       'for mail_code: %s' % self.mail_code))

        # Save central object/instance
        self.object = self.get_object(**kwargs)

        # Digest the templates
        mail_template = loader.get_template('mail_templates/%s.html' % self.mail_code)
        if self.instance and self.mail_data.get('context_object'):
            kwargs[self.mail_data['context_object']] = self.instance
        self.mail_template = mail_template.render(kwargs)

        # Gather Recipients data
        self.original_recipient = self._validate_single_entry(self.mail_data.get('to_address'))[0]

        self.subject = self.mail_data['subject']

    def _validate_single_entry(self, entry):
        """
        entry -- raw email string or path or properties leading to email mail field

        Returns a list of email addresses found.
        """
        if entry and self.object:
            if re.match("[^@]+@[^@]+\.[^@]+", entry):
                # Email string
                return [entry]
            else:
                mail_to = self.object
                for attr in entry.split('.'):
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

    def validate_bcc_list(self):
        """
        bcc_to in the .json file may contain multiple raw email addreses or property paths to
        an email field. The different entries need to be comma separated.
        """
        # Get recipients list. Try to send through BCC to prevent privacy issues!
        self.bcc_list = []
        if self.mail_data.get('bcc_to'):
            for bcc_entry in self.mail_data['bcc_to'].split(','):
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
        """
        Ease workflow by called this wrapper validation method.

        Only to be used when the default data is used, eg. not in the EmailTemplateForm.
        """
        self.validate_message()
        self.validate_bcc_list()
        self.validate_recipients()
        self.save_mail_data()

    def save_mail_data(self):
        self.mail_fields = {
            'subject': self.subject,
            'message': self.message,
            'html_message': self.html_message,
            'recipients': self.recipients,
            'bcc_list': self.bcc_list,
        }

    def set_alternative_sender(self, from_name, from_address):
        """
        Set an alternative from address/name from the default values received from the json
        config file. The arguments only take raw string data, no methods/properties!
        """
        self.mail_data['from_address_name'] = from_name
        self.mail_data['from_address'] = from_address

    def get_object(self, **kwargs):
        if self.object:
            return self.object
        if self.instance:
            return self.instance

        if self.mail_data.get('context_object'):
            return kwargs.get(self.mail_data['context_object'], None)

    def send(self):
        # Send the mail
        email = EmailMultiAlternatives(
            self.mail_fields['subject'],
            self.mail_fields['message'],
            '%s <%s>' % (self.mail_data.get('from_address_name', 'SciPost'),
                         self.mail_data.get('from_address', 'no-reply@scipost.org')),  # From
            self.mail_fields['recipients'],  # To
            bcc=self.mail_fields['bcc_list'],
            reply_to=[self.mail_data.get('from_address', 'no-reply@scipost.org')])
        email.attach_alternative(self.mail_fields['html_message'], 'text/html')
        email.send(fail_silently=False)
        if self.object and hasattr(self.object, 'mail_sent'):
            self.object.mail_sent()
