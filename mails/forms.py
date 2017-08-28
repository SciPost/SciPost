import json

from django import forms
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import loader, Context


class EmailTemplateForm(forms.Form):
    recipient = forms.EmailField()
    subject = forms.CharField(max_length=250)
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 25}))

    def __init__(self, *args, **kwargs):
        self.mail_code = kwargs.pop('mail_code')
        super().__init__(*args)

        # Gather data
        mail_template = loader.get_template('mail_templates/%s.txt' % self.mail_code)
        self.mail_template = mail_template.render(Context(kwargs))
        json_location = '%s/mails/templates/mail_templates/%s.json' % (settings.BASE_DIR,
                                                                       self.mail_code)
        self.mail_data = json.loads(open(json_location).read())

        # Object
        self.object = kwargs.get(self.mail_data.get('context_object'))
        recipient = self.object
        for attr in self.mail_data.get('to_address').split('.'):
            recipient = getattr(recipient, attr)

        # Set the data as initials
        self.fields['text'].initial = self.mail_template
        self.fields['recipient'].initial = recipient
        self.fields['subject'].initial = self.mail_data['subject']

    def send(self):
        # Get text and html
        message = self.cleaned_data['text']
        html_template = loader.get_template('email/general.html')
        html_message = html_template.render(Context({'text': message}))

        # Get recipients list. Always send through BCC to prevent privacy issues!
        bcc_to = self.object
        for attr in self.mail_data.get('bcc_to').split('.'):
            bcc_to = getattr(bcc_to, attr)
        bcc_list = [
            bcc_to,
            self.cleaned_data['recipient']
        ]

        # Send the mail
        email = EmailMultiAlternatives(
            self.cleaned_data['subject'],
            message,
            '%s <%s>' % (self.mail_data.get('from_address_name', 'SciPost'),
                         self.mail_data.get('from_address', 'no-reply@scipost.org')),  # From
            [self.mail_data.get('to_server_address', 'no-reply@scipost.org')],  # To
            bcc=bcc_list,
            reply_to=[self.mail_data.get('from_address', 'no-reply@scipost.org')])
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
