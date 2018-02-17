from django.db import transaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class RegistrationInvitationFormMixin(LoginRequiredMixin, PermissionRequiredMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        send_mail = self.request.POST.get('save', '') == 'save_and_send'
        if send_mail:
            send_mail = self.request.user.has_perm('scipost.can_manage_registration_invitations')
        if send_mail:
            self.object.mail_sent()
            messages.success(self.request, 'Registration Invitation updated and sent')
        else:
            messages.success(self.request, 'Registration Invitation updated')
        return response
