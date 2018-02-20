from django.db import transaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


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
    send_mail = None

    def post(self, request, *args, **kwargs):
        # Intercept the specific submit value before validation the form so `MailEditorMixin`
        # can use this data.
        if self.send_mail is None:
            self.send_mail = request.POST.get('save', '') == 'save_and_send'
            if self.send_mail:
                self.send_mail = request.user.has_perm('scipost.can_manage_registration_invitations')

        # Communicate with the `MailEditorMixin` whether the mails should go out or not.
        self.has_permission_to_send_mail = self.send_mail
        return super().post(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        # Communication with the user.
        model_name = self.object._meta.verbose_name
        model_name = model_name[:1].upper() + model_name[1:]  # Hack it to capitalize the name
        if self.send_mail:
            self.object.mail_sent()
            messages.success(self.request, '{} updated and sent'.format(model_name))
        else:
            messages.success(self.request, '{} updated'.format(model_name))
        return super().form_valid(form)
