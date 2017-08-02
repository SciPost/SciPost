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

# kwargs['invitation'].submission.editor_in_charge.user.email
# initial={'text': mail_template, 'receiver': self.mail_data['to_address'], 'subject': self.mail_data['subject']}
#
#         raise NotImplementedError
#
# class BaseMailUtil(object):
#     mail_sender = 'no-reply@scipost.org'
#     mail_sender_title = ''
#
#     @classmethod
#     def load(cls, _dict, request=None):
#         cls._context = _dict
#         cls._context['request'] = request
#         for var_name in _dict:
#             setattr(cls, var_name, _dict[var_name])
#
#     def _send_mail(cls, template_name, recipients, subject, extra_bcc=None, extra_context={}):
#         """
#         Call this method from a classmethod to send emails.
#         The template will have context variables defined appended from the `load` method.
#
#         Arguments:
#         template_name -- The .html template to use in the mail. The name be used to get the
#                          following two templates:
#                             `email/<template_name>.txt` (non-HTML)
#                             `email/<template_name>.html`
#         recipients -- List of mailaddresses to send to mail to.
#         subject -- The subject of the mail.
#         """

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
            [self.mail_data.get('from_address', 'no-reply@scipost.org')],  # To
            bcc=bcc_list,
            reply_to=[self.mail_data.get('from_address', 'no-reply@scipost.org')])
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
