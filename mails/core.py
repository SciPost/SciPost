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

from .exceptions import ConfigurationError


class MailEngine:
    """
    This engine processes the configuration and template files to be saved into the database in
    the MailLog table.
    """

    _required_parameters = ['recipient_list', 'subject', 'from_email']
    _possible_parameters = ['recipient_list', 'subject', 'from_email', 'from_name', 'bcc']
    _email_fields = ['recipient_list', 'from_email', 'bcc']
    _processed_template = False
    _mail_sent = False

    def __init__(self, mail_code, subject='', recipient_list=[], bcc=[], from_email='',
            from_name='', context_object_name='', **kwargs):
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
            'bcc': bcc,
            'subject': subject,
            'from_name': from_name,
            'from_email': from_email,
            'recipient_list': recipient_list,
            'context_object_name': context_object_name,
        }

        # # Quick check given parameters
        # if from_email:
        #     if not isinstance(from_email, str):
        #         raise TypeError('"from_email" argument must be a string')
        # if recipient_list and not isinstance(recipient_list, list):
        #     raise TypeError('"recipient_list" argument must be a list')
        # if bcc and not isinstance(bcc, list):
        #     raise TypeError('"bcc" argument must be a list')
        self.template_variables = kwargs

    def __repr__(self):
        return '<%(cls)s code="%(code)s", validated=%(validated)s sent=%(sent)s>' % {
            'cls': self.__class__.__name__,
            'code': self.mail_code,
            'validated': hasattr(self, 'mail_data'),
            'sent': self._mail_sent,
        }

    def validate(self, render_template=False):
        """Check if MailEngine is valid and ready for sending."""
        self._read_configuration_file()
        self._detect_and_save_object()
        self._check_template_exists()
        self._validate_configuration()
        if render_template:
            self.render_template()

    def render_template(self, html_message=None):
        """
        Render the template associated with the mail_code. If html_message is given,
        use this as a template instead.
        """
        if html_message:
            self.mail_data['html_message'] = html_message
        else:
            mail_template = get_template('email/%s.html' % self.mail_code)
            self.mail_data['html_message'] = mail_template.render(self.template_variables)  # Damn slow.

        # Transform to non-HTML version.
        handler = HTML2Text()
        self.mail_data['message'] = handler.handle(self.mail_data['html_message'])
        self._processed_template = True

    def send_mail(self):
        """Send the mail."""
        if self._mail_sent:
            # Prevent double sending when using a Django form.
            return
        elif not hasattr(self, 'mail_data'):
            raise ValueError(
                "The mail: %s could not be sent because the data didn't validate." % self.mail_code)

        email = EmailMultiAlternatives(
            self.mail_data['subject'],
            self.mail_data['message'],
            '%s <%s>' % (
                self.mail_data.get('from_name', 'SciPost'),
                self.mail_data.get('from_email', 'noreply@scipost.org')),
            self.mail_data['recipient_list'],
            bcc=self.mail_data['bcc'],
            reply_to=[
                self.mail_data.get('from_email', 'noreply@scipost.org')
            ],
            headers={
                'delayed_processing': not self._processed_template,
                'content_object': self.template_variables['object'],
                'mail_code': self.mail_code,
            })

        # Send html version if available
        if 'html_message' in self.mail_data:
            email.attach_alternative(self.mail_data['html_message'], 'text/html')

        email.send(fail_silently=False)
        self._mail_sent = True

        if self.template_variables['object'] and hasattr(self.template_variables['object'], 'mail_sent'):
            self.instance.mail_sent()

    def _detect_and_save_object(self):
        """
        Detect if less than or equal to one object exists and save it, else raise exception.
        Stick to Django's convention of saving it as a central `object` variable.
        """
        object = None
        context_object_name = None

        if 'context_object_name' in self.mail_data:
            context_object_name = self.mail_data['context_object_name']

        if 'object' in self.template_variables:
            object = self.template_variables['object']
        elif 'instance' in self.template_variables:
            object = self.template_variables['instance']
        elif context_object_name and context_object_name in self.template_variables:
            object = self.template_variables[context_object_name]
        else:
            for key, var in self.template_variables.items():
                if isinstance(var, models.Model):
                    if object:
                        raise ValueError('Multiple db instances are given. Please specify which object to use.')
                    else:
                        object = var
        self.template_variables['object'] = object

        if not context_object_name and isinstance(object, models.Model):
            context_object_name = self.template_variables['object']._meta.model_name

        if context_object_name and object:
            self.template_variables[context_object_name] = object


    def _read_configuration_file(self):
        """Retrieve default configuration for specific mail_code."""
        json_location = '%s/templates/email/%s.json' % (settings.BASE_DIR, self.mail_code)

        try:
            self.mail_data = json.loads(open(json_location).read())
        except OSError:
            raise ImportError('No configuration file found. Mail code: %s' % self.mail_code)

        # Check if configuration file is valid.
        if 'subject' not in self.mail_data:
            raise ConfigurationError('key "subject" is missing.')
        if 'recipient_list' not in self.mail_data:
            raise ConfigurationError('key "recipient_list" is missing.')

        # Overwrite mail data if parameters are given.
        for key, val in self.extra_config.items():
            if val or key not in self.mail_data:
                self.mail_data[key] = val

    def _check_template_exists(self):
        """Save template or raise TemplateDoesNotExist."""
        self._template = get_template('email/%s.html' % self.mail_code)

    def _validate_configuration(self):
        """Check if all required data is given via either configuration or extra parameters."""

        # Check data is complete
        if not all(key in self.mail_data for key in self._required_parameters):
            txt = 'Not all required parameters are given in the configuration file or on instantiation.'
            txt += ' Check required parameters: {}'.format(self._required_parameters)
            raise ConfigurationError(txt)

        # Check all configuration value types
        for email_key in ['subject', 'from_email', 'from_name']:
            if email_key in self.mail_data and self.mail_data[email_key]:
                if not isinstance(self.mail_data[email_key], str):
                    raise ConfigurationError('"%(key)s" argument must be a string' % {
                        'key': email_key,
                    })
        for email_key in ['recipient_list', 'bcc']:
            if email_key in self.mail_data and self.mail_data[email_key]:
                if not isinstance(self.mail_data[email_key], list):
                    raise ConfigurationError('"%(key)s" argument must be a list' % {
                        'key': email_key,
                    })

        # Validate all email addresses
        for email_key in self._email_fields:
            if email_key in self.mail_data:
                if isinstance(self.mail_data[email_key], list):
                    for i, email in enumerate(self.mail_data[email_key]):
                        self.mail_data[email_key][i] = self._validate_email_addresses(email)
                else:
                    self.mail_data[email_key] = self._validate_email_addresses(self.mail_data[email_key])

    def _validate_email_addresses(self, entry):
        """Return email address given raw email or database relation given in `entry`."""
        if re.match("[^@]+@[^@]+\.[^@]+", entry):
            # Email string
            return entry
        elif self.template_variables['object']:
            mail_to = self.template_variables['object']
            for attr in entry.split('.'):
                try:
                    mail_to = getattr(mail_to, attr)
                    if inspect.ismethod(mail_to):
                        mail_to = mail_to()
                except AttributeError:
                    # Invalid property/mail
                    raise KeyError('The property (%s) does not exist.' % entry)
            return mail_to
        raise KeyError('Neither an email adress nor db instance is given.')

    # def pre_validation(self, *args, **kwargs):
    #     """Validate the incoming data to initiate a specific mail."""
    #     self.mail_code = kwargs.pop('mail_code')
    #     self.instance = kwargs.pop('instance', None)
    #     kwargs['object'] = self.instance  # Similar template nomenclature as Django.
    #     self.mail_data = {
    #         'subject': kwargs.pop('subject', ''),
    #         'to_address': kwargs.pop('to', ''),
    #         'bcc_to': kwargs.pop('bcc', ''),
    #         'from_address_name': kwargs.pop('from_name', 'SciPost'),
    #         'from_address': kwargs.pop('from', 'no-reply@scipost.org'),
    #     }
    #
    #     # Gather meta data
    #     json_location = '%s/templates/email/%s.json' % (settings.BASE_DIR, self.mail_code)
    #
        # try:
        #     self.mail_data.update(json.loads(open(json_location).read()))
        # except OSError:
        #     if not self.mail_data['subject']:
        #         raise NotImplementedError(('You did not create a valid .html and .json file '
        #                                    'for mail_code: %s' % self.mail_code))
    #
    #     # Save central object/instance if not already
    #     self.instance = self.get_object(**kwargs)
    #
    #     # Digest the templates
        # if not self.delayed_processing:
        #     mail_template = loader.get_template('email/%s.html' % self.mail_code)
        #     if self.instance and self.mail_data.get('context_object'):
        #         kwargs[self.mail_data['context_object']] = self.instance
        #     self.mail_template = mail_template.render(kwargs)  # Damn slow.
    #
    #     # Gather Recipients data
    #     try:
    #         self.original_recipient = self._validate_single_entry(self.mail_data.get('to_address'))[0]
    #     except IndexError:
    #         self.original_recipient = ''
    #
    #     self.subject = self.mail_data['subject']
    #
    # def get_object(self, **kwargs):
    #     if self.instance:
    #         return self.instance
    #
    #     if self.mail_data.get('context_object'):
    #         return kwargs.get(self.mail_data['context_object'], None)
    #
    # def _validate_single_entry(self, entry):
    #     """
    #     entry -- raw email string or path or properties leading to email mail field
    #
    #     Returns a list of email addresses found.
    #     """
    #         if entry and self.instance:
    #         if re.match("[^@]+@[^@]+\.[^@]+", entry):
    #             # Email string
    #             return [entry]
    #         else:
                # mail_to = self.instance
                # for attr in entry.split('.'):
                #     try:
                #         mail_to = getattr(mail_to, attr)
                #         if inspect.ismethod(mail_to):
                #             mail_to = mail_to()
                #     except AttributeError:
                #         # Invalid property/mail
                #         return []
                #
                # if not isinstance(mail_to, list):
                #     return [mail_to]
                # else:
                #     return mail_to
    #     elif re.match("[^@]+@[^@]+\.[^@]+", entry):
    #         return [entry]
    #     else:
    #         return []
    # #
    # def validate_bcc_list(self):
    #     """
    #     bcc_to in the .json file may contain multiple raw email addreses or property paths to
    #     an email field. The different entries need to be comma separated.
    #     """
    #     # Get recipients list. Try to send through BCC to prevent privacy issues!
    #     self.bcc_list = []
    #     if self.mail_data.get('bcc_to'):
    #         for bcc_entry in self.mail_data['bcc_to'].split(','):
    #             self.bcc_list += self._validate_single_entry(bcc_entry)
    #
    # def validate_recipients(self):
    #     # Check the send list
    #     if isinstance(self.original_recipient, list):
    #         recipients = self.original_recipient
    #     elif not isinstance(self.original_recipient, str):
    #         try:
    #             recipients = list(self.original_recipient)
    #         except TypeError:
    #             recipients = [self.original_recipient]
    #     else:
    #         recipients = [self.original_recipient]
    #     recipients = list(recipients)
    #
    #     # Check if email needs to be taken from an instance
    #     _recipients = []
    #     for recipient in recipients:
    #         if isinstance(recipient, Contributor):
    #             _recipients.append(recipient.user.email)
    #         elif isinstance(recipient, get_user_model()):
    #             _recipients.append(recipient.email)
    #         elif isinstance(recipient, str):
    #             _recipients.append(recipient)
    #     self.recipients = _recipients
    #
    # def validate_message(self):
        # if not self.html_message:
        #     self.html_message = self.mail_template
        # handler = HTML2Text()
        # self.message = handler.handle(self.html_message)
    #
    # def validate(self):
    #     """Execute different validation methods.
    #
    #     Only to be used when the default data is used, eg. not in the EmailTemplateForm.
    #     """
    #     self.validate_message()
    #     self.validate_bcc_list()
    #     self.validate_recipients()
    #     self.save_mail_data()
    #
    # def save_mail_data(self):
    #     """Save mail validated mail data; update default values of mail data."""
    #     self.mail_data.update({
    #         'subject': self.subject,
    #         'message': self.message,
    #         'html_message': self.html_message,
    #         'recipients': self.recipients,
    #         'bcc_list': self.bcc_list,
    #     })
    #
    # def set_alternative_sender(self, from_name, from_address):
    #     """TODO: REMOVE; DEPRECATED
    #
    #     Set an alternative from address/name from the default values received from the json
    #     config file. The arguments only take raw string data, no methods/properties!
    #     """
    #     self.mail_data['from_address_name'] = from_name
    #     self.mail_data['from_address'] = from_address
    #
    # def send(self):
    #     """Send the mail assuming `mail_data` is validated and complete."""
    #     if self.mail_sent:
    #         # Prevent double sending when using a Django form.
    #         return
    #
    #     email = EmailMultiAlternatives(
    #         self.mail_data['subject'],
    #         self.mail_data['message'],
    #         '%s <%s>' % (self.mail_data['from_address_name'], self.mail_data['from_address']),
    #         self.mail_data['recipients'],
    #         bcc=self.mail_data['bcc_list'],
    #         reply_to=[self.mail_data['from_address']],
    #         headers={
    #             'delayed_processing': self.delayed_processing,
    #             'content_object': self.get_object(),
    #             'mail_code': self.mail_code,
    #         })
    #
    #     # Send html version if available
    #     if 'html_message' in self.mail_data:
    #         email.attach_alternative(self.mail_data['html_message'], 'text/html')
    #
    #     email.send(fail_silently=False)
    #     self.mail_sent = True
    #
        # if self.instance and hasattr(self.instance, 'mail_sent'):
        #     self.instance.mail_sent()
