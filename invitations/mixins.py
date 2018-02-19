from django.db import transaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .utils import Utils


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


class SaveAndSendFormMixin:
    """
    Use the Save or Save and Send option to send the mail out after form is valid.
    """
    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        send_mail = self.request.POST.get('save', '') == 'save_and_send'
        if send_mail:
            # Confirm permissions for user
            send_mail = self.request.user.has_perm('scipost.can_manage_registration_invitations')
        model_name = self.object._meta.verbose_name
        if send_mail:
            self.object.mail_sent()
            Utils.load({model_name: self.object})
            getattr(Utils, self.utils_email_method)()
            messages.success(self.request, '{} updated and sent'.format(model_name))
        else:
            messages.success(self.request, '{} updated'.format(model_name))
        return response
