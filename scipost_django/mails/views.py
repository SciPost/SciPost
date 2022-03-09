__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_text
from django.views.generic.edit import UpdateView

from .forms import EmailForm, HiddenDataForm


class MailViewBase:
    """Send a templated email after being edited by user."""

    form_class = None
    mail_code = None
    mail_config = {}
    mail_variables = {}
    fail_silently = True

    def __init__(self, *args, **kwargs):
        if not self.mail_code:
            raise AttributeError(
                self.__class__.__name__ + " object has no attribute `mail_code`"
            )
        super().__init__(*args, **kwargs)
        self.mail_form = None

    def can_send_mail(self):
        """Overwrite method to control permissions for sending mails."""
        return True

    def get_mail_config(self):
        return self.mail_config


class MailFormView(MailViewBase, UpdateView):
    """
    MailUpdateView acts as a base class-based form view, but will intercept the POST request
    of the original form. It'll render the email edit form and save/send both after validation.
    """

    def get_template_names(self):
        """The mail editor form has its own template."""
        if self.mail_form and not self.mail_form.is_valid():
            return ["mails/mail_form.html"]
        return super().get_template_names()

    def post(self, request, *args, **kwargs):
        """Save forms or intercept the request."""
        self.object = None
        if hasattr(self, "get_object"):
            self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            self.mail_form = EmailForm(
                request.POST or None,
                csp_nonce=self.request.csp_nonce,
                mail_code=self.mail_code,
                instance=self.object,
                **self.get_mail_config(),
                **self.mail_variables
            )
            if self.mail_form.is_valid():
                return self.form_valid(form)

            return self.render_to_response(
                self.get_context_data(
                    form=self.mail_form, transfer_data_form=HiddenDataForm(form)
                )
            )
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """If both the regular form and mailing form are valid, save both."""
        response = super().form_valid(form)
        try:
            if not self.can_send_mail():
                if self.fail_silently:
                    return response
                else:
                    raise PermissionDenied(
                        "You are not allowed to send mail: %s." % self.mail_code
                    )
            self.mail_form.save()
        except AttributeError:
            # self.mail_form is None
            raise AttributeError(
                "Did you check the order in which %(cls)s inherits MailView?"
                % {
                    "cls": self.__class__.__name__,
                }
            )
        messages.success(self.request, "Mail sent")
        return response

    def get_success_url(self):
        """
        Returns the supplied URL.
        """
        if self.success_url:
            if hasattr(self, "object") and self.object:
                url = self.success_url.format(**self.object.__dict__)
            else:
                url = force_text(self.success_url)
        elif hasattr(self, "object") and self.object:
            try:
                url = self.object.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the Model."
                )
        else:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return url


class MailView(MailViewBase, UpdateView):
    form_class = EmailForm
    template_name = "mails/mail_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["mail_code"] = self.mail_code
        kwargs["instance"] = self.get_object()
        kwargs["csp_nonce"] = self.request.csp_nonce
        kwargs.update(**self.get_mail_config())
        kwargs.update(**self.mail_variables)
        return kwargs

    def form_valid(self, form):
        """If both the regular form and mailing form are valid, save both."""
        if not self.can_send_mail():
            if self.fail_silently:
                return HttpResponseRedirect(self.get_success_url())
            else:
                raise PermissionDenied(
                    "You are not allowed to send mail: %s." % self.mail_code
                )
        messages.success(self.request, "Mail sent")
        return super().form_valid(form)


class MailEditorSubview:
    """
    This subview works as an interrupter for function based views.

    If a FBV is completed, the MailEditingSubview will interrupt the request and
    provide a form that give the user the possibility to edit a template based email before
    sending it.
    """

    template_name = "mails/mail_form.html"

    def __init__(
        self, request, mail_code, context=None, header_template=None, **kwargs
    ):
        self.mail_code = mail_code
        self.context = context or {}
        self.request = request
        self.header_template = header_template
        self.mail_form = EmailForm(
            request.POST or None,
            csp_nonce=self.request.csp_nonce,
            mail_code=mail_code,
            **kwargs
        )
        self._is_valid = False

    def interrupt(self):
        """
        Interrupt request by rendering the templated email form.

        The `request` should be an HttpRequest instance that should be captured
        and be included into the response of the interrupted response. Currently only
        POST requests are supported.
        """
        self.context["form"] = self.mail_form
        self.context["header_template"] = self.header_template
        if "object" in self.mail_form.engine.template_variables:
            self.context["object"] = self.mail_form.engine.template_variables["object"]
        else:
            self.context["object"] = None
        return render(self.request, self.template_name, self.context)

    def is_valid(self):
        """See if data is returned and valid."""
        self._is_valid = self.mail_form.is_valid()
        return self._is_valid

    def send_mail(self):
        """Send email as returned by user."""
        if not self._is_valid:
            raise ValueError(
                "The mail: %s could not be sent because the data didn't validate."
                % self.mail_code
            )
        return self.mail_form.save()


class MailEditorSubviewHTMX(MailEditorSubview):
    template_name = "mails/_hx_mail_form.html"


class MailEditorMixin:
    """Deprecated."""

    pass
