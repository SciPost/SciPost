from django.db import transaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .constants import INVITATION_EDITORIAL_FELLOW
from .models import RegistrationInvitation


class RequestArgumentMixin:
    """
    Use the WSGIRequest as an argument in the form.
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermissionsMixin(LoginRequiredMixin, PermissionRequiredMixin):
    pass


class BaseFormViewMixin:
    send_mail = None

    @transaction.atomic
    def form_valid(self, form):
        # Communication with the user.
        model_name = self.object._meta.verbose_name
        model_name = model_name[:1].upper() + model_name[1:]  # Hack it to capitalize the name

        if self.send_mail:
            self.object.mail_sent(user=self.request.user)
            messages.success(self.request, '{} updated and sent'.format(model_name))
        else:
            messages.success(self.request, '{} updated'.format(model_name))
        return super().form_valid(form)


class SendMailFormMixin(BaseFormViewMixin):
    """
    Send mail out if form is valid.
    """
    def post(self, request, *args, **kwargs):
        # Intercept the specific submit value before validation the form so `MailEditorMixin`
        # can use this data.
        if self.send_mail is None:
            # Communicate with the `MailEditorMixin` whether the mails should go out or not.
            self.send_mail = request.user.has_perm('scipost.can_manage_registration_invitations')
            self.has_permission_to_send_mail = self.send_mail

        if isinstance(self.object, RegistrationInvitation):
            if self.object.invitation_type == INVITATION_EDITORIAL_FELLOW:
                self.alternative_from_address = ('J-S Caux', 'jscaux@scipost.org')
        return super().post(request, *args, **kwargs)


class SaveAndSendFormMixin(BaseFormViewMixin):
    """
    Use the Save or Save and Send option to send the mail out after form is valid.
    """
    def post(self, request, *args, **kwargs):
        # Intercept the specific submit value before validation the form so `MailEditorMixin`
        # can use this data.
        if self.send_mail is None:
            self.send_mail = request.POST.get('save', '') in ['save_and_send', 'send_from_editor']
            if self.send_mail:
                self.send_mail = request.user.has_perm('scipost.can_manage_registration_invitations')

        # Communicate with the `MailEditorMixin` whether the mails should go out or not.
        self.has_permission_to_send_mail = self.send_mail
        instance = self.get_object()
        if isinstance(instance, RegistrationInvitation):
            if instance.invitation_type == INVITATION_EDITORIAL_FELLOW:
                self.alternative_from_address = ('J-S Caux', 'jscaux@scipost.org')
        return super().post(request, *args, **kwargs)
