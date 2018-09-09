__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .mixins import MailUtilsMixin
from .widgets import SummernoteEditor


class EmailTemplateForm(forms.Form, MailUtilsMixin):
    subject = forms.CharField(max_length=250, label="Subject*")
    text = forms.CharField(widget=SummernoteEditor, label="Text*")
    extra_recipient = forms.EmailField(label="Optional: bcc this email to", required=False)
    prefix = 'mail_form'

    def __init__(self, *args, **kwargs):
        self.pre_validation(*args, **kwargs)

        # This form shouldn't be is_bound==True is there is any non-relavant POST data given.
        data = args[0] if args else {}
        if not data:
            data = {}
        if '%s-subject' % self.prefix in data.keys():
            data = {
                '%s-subject' % self.prefix: data.get('%s-subject' % self.prefix),
                '%s-text' % self.prefix: data.get('%s-text' % self.prefix),
                '%s-extra_recipient' % self.prefix: data.get('%s-extra_recipient' % self.prefix),
            }
        elif kwargs.get('data', False):
            data = {
                '%s-subject' % self.prefix: kwargs['data'].get('%s-subject' % self.prefix),
                '%s-text' % self.prefix: kwargs['data'].get('%s-text' % self.prefix),
                '%s-extra_recipient' % self.prefix: kwargs['data'].get('%s-extra_recipient' % self.prefix),
            }
        else:
            data = None
        super().__init__(data or None)

        if not self.original_recipient:
            self.fields['extra_recipient'].label = "Send this email to"
            self.fields['extra_recipient'].required = True

        # Set the data as initials
        self.fields['text'].initial = self.mail_template
        self.fields['subject'].initial = self.mail_data['subject']

    def save_data(self):
        # Get text and html
        self.html_message = self.cleaned_data['text']
        self.subject = self.cleaned_data['subject']
        self.validate_message()
        self.validate_bcc_list()

        # Get recipients list. Try to send through BCC to prevent privacy issues!
        if self.cleaned_data.get('extra_recipient') and self.original_recipient:
            self.bcc_list.append(self.cleaned_data.get('extra_recipient'))
        elif self.cleaned_data.get('extra_recipient') and not self.original_recipient:
            self.original_recipient = [self.cleaned_data.get('extra_recipient')]
        elif not self.original_recipient:
            self.add_error('extra_recipient', 'Please fill the bcc field to send the mail.')

        self.validate_recipients()
        self.save_mail_data()

    def clean(self):
        data = super().clean()
        self.save_data()
        return data

    def save(self):
        """Because Django uses .save() by default..."""
        self.send()
        return self.instance



class HiddenDataForm(forms.Form):
    def __init__(self, form, *args, **kwargs):
        super().__init__(form.data, *args, **kwargs)
        for name, field in form.fields.items():
            self.fields[name] = field
            self.fields[name].widget = forms.HiddenInput()
