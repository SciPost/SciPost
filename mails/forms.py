import re
import json
import inspect
from html2text import HTML2Text

from django import forms
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template import loader

from scipost.models import Contributor

from .widgets import SummernoteEditor


class EmailTemplateForm(forms.Form):
    subject = forms.CharField(max_length=250, label="Subject*")
    text = forms.CharField(widget=SummernoteEditor, label="Text*")
    extra_recipient = forms.EmailField(label="Optional: bcc this email to", required=False)

    def __init__(self, *args, **kwargs):
        self.mail_code = kwargs.pop('mail_code')
        self.mail_fields = None
        super().__init__(*args)

        # Gather data
        mail_template = loader.get_template('mail_templates/%s.html' % self.mail_code)
        mail_template = mail_template.render(kwargs)
        # self.doc = html.fromstring(mail_template)
        # self.doc2 = self.doc.text_content()
        # print(self.doc2)

        json_location = '%s/mails/templates/mail_templates/%s.json' % (settings.BASE_DIR,
                                                                       self.mail_code)
        self.mail_data = json.loads(open(json_location).read())

        # Object
        self.object = kwargs.get(self.mail_data.get('context_object', ''), None)
        self.recipient = None
        if self.object:
            recipient = self.object
            for attr in self.mail_data.get('to_address').split('.'):
                recipient = getattr(recipient, attr)
                if inspect.ismethod(recipient):
                    recipient = recipient()
            self.recipient = recipient

        if not self.recipient:
            self.fields['extra_recipient'].label = "Send this email to"
            self.fields['extra_recipient'].required = True

        # Set the data as initials
        self.fields['text'].initial = mail_template
        self.fields['subject'].initial = self.mail_data['subject']

    def save_data(self):
        # Get text and html
        html_message = self.cleaned_data['text']
        handler = HTML2Text()
        message = handler.handle(html_message)

        # Get recipients list. Try to send through BCC to prevent privacy issues!
        bcc_list = []
        if self.mail_data.get('bcc_to', False) and self.object:
            if re.match("[^@]+@[^@]+\.[^@]+", self.mail_data.get('bcc_to')):
                bcc_list = [self.mail_data.get('bcc_to')]
            else:
                bcc_to = self.object
                for attr in self.mail_data.get('bcc_to').split('.'):
                    bcc_to = getattr(bcc_to, attr)

                if not isinstance(bcc_to, list):
                    bcc_list = [bcc_to]
                else:
                    bcc_list = bcc_to
        elif re.match("[^@]+@[^@]+\.[^@]+", self.mail_data.get('bcc_to', '')):
            bcc_list = [self.mail_data.get('bcc_to')]

        if self.cleaned_data.get('extra_recipient') and self.recipient:
            bcc_list.append(self.cleaned_data.get('extra_recipient'))
        elif self.cleaned_data.get('extra_recipient') and not self.recipient:
            self.recipient = [self.cleaned_data.get('extra_recipient')]
        elif not self.recipient:
            self.add_error('extra_recipient', 'Please fill the bcc field to send the mail.')

        # Check the send list
        if isinstance(self.recipient, list):
            recipients = self.recipient
        elif not isinstance(self.recipient, str):
            try:
                recipients = list(self.recipient)
            except TypeError:
                recipients = [self.recipient]
        else:
            recipients = [self.recipient]
        recipients = list(recipients)

        # Check if email needs to be taken from instance
        _recipients = []
        for recipient in recipients:
            if isinstance(recipient, Contributor):
                _recipients.append(recipient.user.email)
            elif isinstance(recipient, get_user_model()):
                _recipients.append(recipient.email)
            elif isinstance(recipient, str):
                _recipients.append(recipient)

        self.mail_fields = {
            'subject': self.cleaned_data['subject'],
            'message': message,
            'html_message': html_message,
            'recipients': _recipients,
            'bcc_list': bcc_list,
        }

    def clean(self):
        data = super().clean()
        self.save_data()
        return data

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
