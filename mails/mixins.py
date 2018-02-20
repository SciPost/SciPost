import re
import json
import inspect
from html2text import HTML2Text

from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template import loader

from scipost.models import Contributor


from . import forms


class MailEditorMixin:
    """
    Use MailEditorMixin in edit CBVs to automatically implement the mail editor as
    a post-form_valid hook.

    The view must specify the `mail_code` variable.
    """
    object = None
    mail_form = None
    has_permission_to_send_mail = True

    def __init__(self, *args, **kwargs):
        if not self.mail_code:
            raise AttributeError(self.__class__.__name__ + ' object has no attribute `mail_code`')
        super().__init__(*args, **kwargs)

    def get_template_names(self):
        """
        The mail editor form has its own template.
        """
        if self.mail_form and not self.mail_form.is_valid():
            return ['mails/mail_form.html']
        return super().get_template_names()

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests, but interpect the data if the mail form data isn't valid.
        """
        if not self.has_permission_to_send_mail:
            # Don't use the mail form; don't send out the mail.
            return super().post(request, *args, **kwargs)
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            self.mail_form = forms.EmailTemplateForm(request.POST or None,
                                                     mail_code=self.mail_code,
                                                     instance=self.object)
            if self.mail_form.is_valid():
                return self.form_valid(form)

            return self.render_to_response(
                self.get_context_data(form=self.mail_form,
                                      transfer_data_form=forms.HiddenDataForm(form)))
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        If both the regular form and mailing form are valid, save the form and run the mail form.
        """
        # Don't use the mail form; don't send out the mail.
        if not self.has_permission_to_send_mail:
            return super().form_valid(form)

        try:
            self.mail_form.send()
        except AttributeError:
            # self.mail_form is None
            raise AttributeError('Did you check the order in which MailEditorMixin is used?')
        messages.success(self.request, 'Mail sent')
        return super().form_valid(form)


class MailUtilsMixin:
    """
    This mixin takes care of inserting the default data into the Utils or Form.
    """
    object = None
    mail_fields = {}
    mail_template = ''
    html_message = ''
    message = ''

    def __init__(self, *args, **kwargs):
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
        self.original_recipient = ''
        if self.object:
            recipient = self.object
            for attr in self.mail_data.get('to_address').split('.'):
                recipient = getattr(recipient, attr)
                if inspect.ismethod(recipient):
                    recipient = recipient()
            self.original_recipient = recipient

        self.subject = self.mail_data['subject']


    def validate_recipients(self):
        # Get recipients list. Try to send through BCC to prevent privacy issues!
        self.bcc_list = []
        if self.mail_data.get('bcc_to', False) and self.object:
            if re.match("[^@]+@[^@]+\.[^@]+", self.mail_data.get('bcc_to')):
                self.bcc_list = [self.mail_data.get('bcc_to')]
            else:
                bcc_to = self.object
                for attr in self.mail_data.get('bcc_to').split('.'):
                    bcc_to = getattr(bcc_to, attr)

                if not isinstance(bcc_to, list):
                    self.bcc_list = [bcc_to]
                else:
                    self.bcc_list = bcc_to
        elif re.match("[^@]+@[^@]+\.[^@]+", self.mail_data.get('bcc_to', '')):
            self.bcc_list = [self.mail_data.get('bcc_to')]

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
