__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.shortcuts import render

from .forms import EmailTemplateForm, HiddenDataForm


class MailEditingSubView(object):
    alternative_from_address = None  # Tuple: ('from_name', 'from_address')

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

    def set_alternative_sender(self, from_name, from_address):
        self.alternative_from_address = (from_name, from_address)

    def is_valid(self):
        return self.mail_form.is_valid()

    def send(self):
        if self.alternative_from_address:
            self.mail_form.set_alternative_sender(
                self.alternative_from_address[0], self.alternative_from_address[1])
        return self.mail_form.send()

    def return_render(self):
        self.context['form'] = self.mail_form
        return render(self.request, self.template_name, self.context)


class MailEditorMixin:
    """
    Use MailEditorMixin in edit CBVs to automatically implement the mail editor as
    a post-form_valid hook.

    The view must specify the `mail_code` variable.
    """
    object = None
    mail_form = None
    has_permission_to_send_mail = True
    alternative_from_address = None  # Tuple: ('from_name', 'from_address')

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
            self.mail_form = EmailTemplateForm(request.POST or None, mail_code=self.mail_code,
                                               instance=self.object)
            if self.mail_form.is_valid():
                return self.form_valid(form)

            return self.render_to_response(
                self.get_context_data(form=self.mail_form,
                                      transfer_data_form=HiddenDataForm(form)))
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        If both the regular form and mailing form are valid, save the form and run the mail form.
        """
        # Don't use the mail form; don't send out the mail.
        if not self.has_permission_to_send_mail:
            return super().form_valid(form)

        if self.alternative_from_address:
            # Set different from address if given.
            self.mail_form.set_alternative_sender(
                self.alternative_from_address[0], self.alternative_from_address[1])

        response = super().form_valid(form)
        try:
            self.mail_form.send()
        except AttributeError:
            # self.mail_form is None
            raise AttributeError('Did you check the order in which MailEditorMixin is used?')
        messages.success(self.request, 'Mail sent')
        return response
