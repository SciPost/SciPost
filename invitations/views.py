from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView

from .forms import RegistrationInvitationForm, RegistrationInvitationReminderForm,\
    RegistrationInvitationMarkForm, RegistrationInvitationMapToContributorForm,\
    CitationNotificationForm, SuggestionSearchForm, RegistrationInvitationFilterForm,\
    CitationNotificationProcessForm, RegistrationInvitationAddCitationForm
from .mixins import RequestArgumentMixin, PermissionsMixin, SaveAndSendFormMixin, SendMailFormMixin
from .models import RegistrationInvitation, CitationNotification

from scipost.models import Contributor
from mails.mixins import MailEditorMixin


class RegistrationInvitationsView(PermissionsMixin, ListView):
    permission_required = 'scipost.can_create_registration_invitations'
    queryset = RegistrationInvitation.objects.drafts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count_in_draft'] = RegistrationInvitation.objects.drafts().count()
        context['count_pending'] = RegistrationInvitation.objects.sent().count()
        search_form = RegistrationInvitationFilterForm(self.request.GET or None)
        if search_form.is_valid():
            context['object_list'] = search_form.search(context['object_list'])
        context['object_list'] = context['object_list'].order_by(
            'status', 'date_sent_last', 'last_name')
        context['search_form'] = search_form
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        if not self.request.user.has_perm('scipost.can_invite_fellows'):
            qs = qs.not_for_fellows()
        return qs


class RegistrationInvitationsSentView(PermissionsMixin, ListView):
    permission_required = 'scipost.can_create_registration_invitations'
    queryset = RegistrationInvitation.objects.sent()
    template_name = 'invitations/registrationinvitation_list_sent.html'


class CitationNotificationsView(PermissionsMixin, ListView):
    permission_required = 'scipost.can_manage_registration_invitations'
    queryset = CitationNotification.objects.unprocessed().prefetch_related(
        'invitation', 'contributor', 'contributor__user')


class CitationNotificationsProcessView(PermissionsMixin, RequestArgumentMixin,
                                       MailEditorMixin, UpdateView):
    permission_required = 'scipost.can_manage_registration_invitations'
    form_class = CitationNotificationProcessForm
    queryset = CitationNotification.objects.unprocessed()
    success_url = reverse_lazy('invitations:citation_notification_list')
    mail_code = 'citation_notification'

    @transaction.atomic
    def form_valid(self, form):
        """
        Form is valid; use the MailEditorMixin to send out the mail if
        (possible) Contributor didn't opt-out from mails.
        """
        form.get_all_notifications().update(processed=True)
        contributor = form.get_all_notifications().filter(contributor__isnull=False).first()
        self.send_mail = (contributor and contributor.accepts_SciPost_emails) or not contributor
        return super().form_valid(form)


@login_required
@permission_required('scipost.can_create_registration_invitations', raise_exception=True)
@transaction.atomic
def create_registration_invitation_or_citation(request):
    """
    Create a new Registration Invitation or Citation Notification, depending whether
    it is meant for an already existing Contributor or not.
    """
    contributors = []
    suggested_invitations = []
    declined_invitations = []

    # Only take specific GET data to prevent for unexpected bound forms.
    search_data = {}
    initial_search_data = {}
    if request.GET.get('last_name'):
        search_data['last_name'] = request.GET['last_name']
    if request.GET.get('prefill-last_name'):
        initial_search_data['last_name'] = request.GET['prefill-last_name']
    suggestion_search_form = SuggestionSearchForm(search_data or None,
                                                  initial=initial_search_data)
    if suggestion_search_form.is_valid():
        contributors, suggested_invitations, declined_invitations = suggestion_search_form.search()
    citation_form = CitationNotificationForm(request.POST or None, contributors=contributors,
                                             prefix='notification', request=request)

    # New citation is related to a Contributor: RegistationInvitation
    invitation_form = RegistrationInvitationForm(request.POST or None, request=request,
                                                 prefix='invitation',
                                                 initial=initial_search_data)
    if invitation_form.is_valid():
        invitation_form.save()
        messages.success(request, 'New Registration Invitation created')
        if request.POST.get('save') == 'save_and_create':
            return redirect('invitations:new')
        return redirect('invitations:list')

    # New citation is related to a Contributor: CitationNotification
    if citation_form.is_valid():
        citation_form.save()
        messages.success(request, 'New Citation Notification created')
        if request.POST.get('save') == 'save_and_create':
            return redirect('invitations:new')
        return redirect('invitations:list')

    context = {
        'suggestion_search_form': suggestion_search_form,
        'citation_form': citation_form,
        'suggested_invitations': suggested_invitations,
        'declined_invitations': declined_invitations,
        'invitation_form': invitation_form,
    }
    return render(request, 'invitations/registrationinvitation_form_add_new.html', context)


class RegistrationInvitationsUpdateView(RequestArgumentMixin, PermissionsMixin,
                                        SaveAndSendFormMixin, MailEditorMixin, UpdateView):
    permission_required = 'scipost.can_create_registration_invitations'
    form_class = RegistrationInvitationForm
    mail_code = 'registration_invitation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitation_form'] = context['form']
        return context

    def get_success_url(self):
        if self.request.POST.get('save') == 'save_and_create':
            return reverse('invitations:new')
        return reverse('invitations:list')

    def get_queryset(self, *args, **kwargs):
        qs = RegistrationInvitation.objects.drafts()
        if not self.request.user.has_perm('scipost.can_invite_fellows'):
            qs = qs.not_for_fellows()
        if not self.request.user.has_perm('scipost.can_manage_registration_invitations'):
            qs = qs.created_by(self.request.user)
        return qs


class RegistrationInvitationsAddCitationView(RequestArgumentMixin, PermissionsMixin, UpdateView):
    permission_required = 'scipost.can_create_registration_invitations'
    form_class = RegistrationInvitationAddCitationForm
    template_name = 'invitations/registrationinvitation_form_add_citation.html'
    success_url = reverse_lazy('invitations:list')
    queryset = RegistrationInvitation.objects.no_response()


class RegistrationInvitationsMarkView(RequestArgumentMixin, PermissionsMixin, UpdateView):
    permission_required = 'scipost.can_manage_registration_invitations'
    queryset = RegistrationInvitation.objects.drafts()
    form_class = RegistrationInvitationMarkForm
    template_name = 'invitations/registrationinvitation_form_mark_as.html'
    success_url = reverse_lazy('invitations:list')


class RegistrationInvitationsMapToContributorView(RequestArgumentMixin, PermissionsMixin,
                                                  UpdateView):
    permission_required = 'scipost.can_manage_registration_invitations'
    model = RegistrationInvitation
    form_class = RegistrationInvitationMapToContributorForm
    template_name = 'invitations/registrationinvitation_form_map_to_contributor.html'
    success_url = reverse_lazy('invitations:list')


class RegistrationInvitationsReminderView(RequestArgumentMixin, PermissionsMixin,
                                          SendMailFormMixin, MailEditorMixin, UpdateView):
    permission_required = 'scipost.can_manage_registration_invitations'
    queryset = RegistrationInvitation.objects.sent()
    success_url = reverse_lazy('invitations:list')
    form_class = RegistrationInvitationReminderForm
    template_name = 'invitations/registrationinvitation_reminder_form.html'
    mail_code = 'registration_invitation_reminder'


class RegistrationInvitationsDeleteView(PermissionsMixin, DeleteView):
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
    invitations = RegistrationInvitation.objects.sent().filter(email__in=contributor_email_list)
    context = {
        'invitations': invitations
    }
    return render(request, 'invitations/registrationinvitation_cleanup.html', context)
