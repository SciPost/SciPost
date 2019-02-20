__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib import messages
from django.shortcuts import render
from django.views.generic.edit import UpdateView

from submissions.models import Submission
from .forms import EmailForm, HiddenDataForm


class MailView(UpdateView):
    """Send a templated email after being edited by user."""

    form_class = None
    mail_code = None
    mail_config = {}

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs['mail_code'] = self.mail_code
    #     kwargs['mail_config'] = self.mail_config
    #     return kwargs
    # object = None
    # mail_form = None
    has_permission_to_send_mail = True
    # alternative_from_address = None  # Tuple: ('from_name', 'from_address')
    # 'mails/mail_form.html'
    def __init__(self, *args, **kwargs):
        if not self.mail_code:
            raise AttributeError(self.__class__.__name__ + ' object has no attribute `mail_code`')
        super().__init__(*args, **kwargs)
        self.mail_form = None

    def get_template_names(self):
        """The mail editor form has its own template."""
        if self.mail_form and not self.mail_form.is_valid():
            return ['mails/mail_form.html']
        return super().get_template_names()

    def post(self, request, *args, **kwargs):
        """Handle POST requests, but intercept the data if the mail form data isn't valid."""
        self.object = None
        if hasattr(self, 'get_object'):
            self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            self.mail_form = EmailForm(
                request.POST or None, mail_code=self.mail_code,
                instance=self.object, **self.mail_config)
            if self.mail_form.is_valid():
                return self.form_valid(form)

            return self.render_to_response(
                self.get_context_data(
                    form=self.mail_form, transfer_data_form=HiddenDataForm(form)))
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """If both the regular form and mailing form are valid, save both."""
        # # Don't use the mail form; don't send out the mail.
        # if not self.has_permission_to_send_mail:
        #     return super().form_valid(form)

        # if self.alternative_from_address:
        #     # Set different from address if given.
        #     self.mail_form.set_alternative_sender(
        #         self.alternative_from_address[0], self.alternative_from_address[1])

        response = super().form_valid(form)
        try:
            self.mail_form.save()
        except AttributeError:
            # self.mail_form is None
            raise AttributeError('Did you check the order in which %(cls)s inherits MailView?' % {
                'cls': self.__class__.__name__,
            })
        messages.success(self.request, 'Mail sent')
        return response


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


class MailEditorMixin:
    """Deprecated."""
    pass
