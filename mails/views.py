__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# from django.contrib import messages
# from django.db import models
# from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic.edit import UpdateView

from submissions.models import Submission
from .forms import EmailForm


class MailView(UpdateView):
    """Send a templated email after being edited by user."""

    template_name = 'mails/mail_form.html'
    form_class = EmailForm
    mail_code = None
    mail_config = {}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mail_code'] = self.mail_code
        kwargs['mail_config'] = self.mail_config
        return kwargs

    # def form_invalid(self, form):
    #     """If the form is valid, save the associated model."""
    #     raise
    #     self.object = form.save()
    #     return super().form_valid(form)



class TestView(MailView):
    """To be removed; exists for testing purposes only."""
    mail_code = 'tests/test_mail_code_1'
    model = Submission
    success_url = '/'


class MailEditorSubview:
    """
    This subview works as an interrupter for function based views.

    If a FBV is completed, the MailEditingSubview will interrupt the request and
    provide a form that give the user the possibility to edit a template based email before
    sending it.
    """

    template_name = 'mails/mail_form.html'

    def __init__(self, request, mail_code, context=None, header_template=None, **kwargs):
        self.mail_code = mail_code
        self.context = context or {}
        self.request = request
        self.header_template = header_template
        self.mail_form = EmailForm(request.POST or None, mail_code=mail_code, **kwargs)
        self._is_valid = False

    def interrupt(self):
        """
        Interrupt request by rendering the templated email form.

        The `request` should be an HttpRequest instance that should be captured
        and be included into the response of the interrupted response. Currently only
        POST requests are supported.
        """
        self.context['form'] = self.mail_form
        self.context['header_template'] = self.header_template
        if 'object' in self.mail_form.engine.template_variables:
            self.context['object'] = self.mail_form.engine.template_variables['object']
        else:
            self.context['object'] = None
        return render(self.request, self.template_name, self.context)

    def is_valid(self):
        """See if data is returned and valid."""
        self._is_valid = self.mail_form.is_valid()
        return self._is_valid

    def send_mail(self):
        """Send email as returned by user."""
        if not self._is_valid:
            raise ValueError(
                "The mail: %s could not be sent because the data didn't validate." % self.mail_code)
        return self.mail_form.save()


class MailEditingSubView:
    """Deprecated."""
    pass
#     alternative_from_address = None  # Tuple: ('from_name', 'from_address')
#
#     def __init__(self, request, mail_code, **kwargs):
#         self.request = request
#         self.context = kwargs.get('context', {})
#         # self.template_name = kwargs.get('template', 'mails/mail_form.html')
#         self.header_template = kwargs.get('header_template', '')
#         self.mail_form = EmailForm(request.POST or None, mail_code=mail_code, **kwargs)
#
#     @property
#     def recipients_string(self):
#         return ', '.join(getattr(self.mail_form, 'mail_data', {}).get('recipients', ['']))
#
#     def add_form(self, form):
#         """DEPRECATED"""
#         self.context['transfer_data_form'] = HiddenDataForm(form)
#
#     def set_alternative_sender(self, from_name, from_address):
#         """DEPRECATED"""
#         self.alternative_from_address = (from_name, from_address)
#
#     def is_valid(self):
#         return self.mail_form.is_valid()
#
#     def send(self):
#         if self.alternative_from_address:
#             self.mail_form.set_alternative_sender(
#                 self.alternative_from_address[0], self.alternative_from_address[1])
#         return self.mail_form.send()
#
#     def return_render(self):
#         self.context['form'] = self.mail_form
#         self.context['header_template'] = self.header_template
#         if hasattr(self.mail_form, 'instance') and self.mail_form.instance:
#             self.context['object'] = self.mail_form.instance
#         else:
#             self.context['object'] = None
#         return render(self.request, self.template_name, self.context)


class MailEditorMixin:
    """Deprecated."""
    pass
    # """
    # Use MailEditorMixin in edit CBVs to automatically implement the mail editor as
    # a post-form_valid hook.
    #
    # The view must specify the `mail_code` variable.
    # """
    # object = None
    # mail_form = None
    # has_permission_to_send_mail = True
    # alternative_from_address = None  # Tuple: ('from_name', 'from_address')
    #
    # def __init__(self, *args, **kwargs):
    #     if not self.mail_code:
    #         raise AttributeError(self.__class__.__name__ + ' object has no attribute `mail_code`')
    #     super().__init__(*args, **kwargs)
    #
    # def get_template_names(self):
    #     """
    #     The mail editor form has its own template.
    #     """
    #     if self.mail_form and not self.mail_form.is_valid():
    #         return ['mails/mail_form.html']
    #     return super().get_template_names()
    #
    # def post(self, request, *args, **kwargs):
    #     """
    #     Handle POST requests, but interpect the data if the mail form data isn't valid.
    #     """
    #     if not self.has_permission_to_send_mail:
    #         # Don't use the mail form; don't send out the mail.
    #         return super().post(request, *args, **kwargs)
    #     self.object = self.get_object()
    #     form = self.get_form()
    #     if form.is_valid():
    #         self.mail_form = EmailForm(request.POST or None, mail_code=self.mail_code,
    #                                            instance=self.object)
    #         if self.mail_form.is_valid():
    #             return self.form_valid(form)
    #
    #         return self.render_to_response(
    #             self.get_context_data(form=self.mail_form,
    #                                   transfer_data_form=HiddenDataForm(form)))
    #     else:
    #         return self.form_invalid(form)
    #
    # def form_valid(self, form):
    #     """
    #     If both the regular form and mailing form are valid, save the form and run the mail form.
    #     """
    #     # Don't use the mail form; don't send out the mail.
    #     if not self.has_permission_to_send_mail:
    #         return super().form_valid(form)
    #
    #     if self.alternative_from_address:
    #         # Set different from address if given.
    #         self.mail_form.set_alternative_sender(
    #             self.alternative_from_address[0], self.alternative_from_address[1])
    #
    #     response = super().form_valid(form)
    #     try:
    #         self.mail_form.send()
    #     except AttributeError:
    #         # self.mail_form is None
    #         raise AttributeError('Did you check the order in which MailEditorMixin is used?')
    #     messages.success(self.request, 'Mail sent')
    #     return response
