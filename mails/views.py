__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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
