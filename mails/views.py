from django.shortcuts import render

from .forms import EmailTemplateForm, HiddenDataForm


class MailEditingSubView(object):
    def __init__(self, request, mail_code, **kwargs):
        self.request = request
        self.context = kwargs.get('context', {})
        self.template_name = kwargs.get('template', 'mails/mail_form.html')
        self.mail_form = EmailTemplateForm(request.POST or None, mail_code=mail_code, **kwargs)

    @property
    def recipients_string(self):
        return ', '.join(getattr(self.mail_form, 'mail_fields', {}).get('recipients', ['']))

    def add_form(self, form):
        self.context['transfer_data_form'] = HiddenDataForm(form)

    def is_valid(self):
        return self.mail_form.is_valid()

    def send(self):
        return self.mail_form.send()

    def return_render(self):
        self.context['form'] = self.mail_form
        return render(self.request, self.template_name, self.context)
