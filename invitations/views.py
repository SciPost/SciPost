from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import RegistrationInvitationForm, RegistrationInvitationReminderForm
from .mixins import RegistrationInvitationFormMixin
from .models import RegistrationInvitation

from scipost.models import Contributor


class RegistrationInvitationsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'scipost.can_create_registration_invitations'
    queryset = RegistrationInvitation.objects.drafts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count_in_draft'] = RegistrationInvitation.objects.drafts().count()
        context['count_pending'] = RegistrationInvitation.objects.pending_response().count()
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        if not self.request.user.has_perm('scipost.can_invite_fellows'):
            qs = qs.not_for_fellows()
        return qs


class PendingRegistrationInvitationsView(RegistrationInvitationsView):
    permission_required = 'scipost.can_manage_registration_invitations'
    queryset = RegistrationInvitation.objects.pending_response()
    template_name = 'invitations/registrationinvitation_pending_list.html'


class RegistrationInvitationsCreateView(RegistrationInvitationFormMixin, CreateView):
    permission_required = 'scipost.can_create_registration_invitations'
    form_class = RegistrationInvitationForm
    model = RegistrationInvitation
    success_url = reverse_lazy('invitations:list')


class RegistrationInvitationsUpdateView(RegistrationInvitationFormMixin, UpdateView):
    permission_required = 'scipost.can_create_registration_invitations'
    form_class = RegistrationInvitationForm
    success_url = reverse_lazy('invitations:list')

    def get_queryset(self, *args, **kwargs):
        qs = RegistrationInvitation.objects.drafts()
        if not self.request.user.has_perm('scipost.can_invite_fellows'):
            qs = qs.not_for_fellows()
        if not self.request.user.has_perm('scipost.can_manage_registration_invitations'):
            qs = qs.invited_by(self.request.user)
        return qs


class RegistrationInvitationsReminderView(RegistrationInvitationFormMixin, UpdateView):
    permission_required = 'scipost.can_manage_registration_invitations'
    queryset = RegistrationInvitation.objects.pending_response()
    form_class = RegistrationInvitationReminderForm
    template_name = 'invitations/registrationinvitation_reminder_form.html'


class RegistrationInvitationsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'scipost.can_manage_registration_invitations'
    model = RegistrationInvitation
    success_url = reverse_lazy('invitations:list')


@login_required
@permission_required('scipost.can_manage_registration_invitations', raise_exception=True)
def cleanup(request):
    """
    Compares the email addresses of invitations with those in the
    database of registered Contributors. Flags overlaps.
    """
    contributor_email_list = Contributor.objects.values_list('user__email', flat=True)
    invitations = RegistrationInvitation.objects.pending_response().filter(
        email__in=contributor_email_list)
    context = {
        'invitations': invitations
    }
    return render(request, 'invitations/registrationinvitation_cleanup.html', context)
