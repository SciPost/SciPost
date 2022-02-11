__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView

from .constants import INVITATION_EDITORIAL_FELLOW
from .forms import (
    RegistrationInvitationForm,
    RegistrationInvitationReminderForm,
    RegistrationInvitationMarkForm,
    RegistrationInvitationMapToContributorForm,
    CitationNotificationForm,
    SuggestionSearchForm,
    RegistrationInvitationFilterForm,
    CitationNotificationProcessForm,
    RegistrationInvitationAddCitationForm,
    RegistrationInvitationMergeForm,
)
from .mixins import RequestArgumentMixin
from .models import RegistrationInvitation, CitationNotification

from scipost.models import Contributor
from scipost.mixins import PaginationMixin, PermissionsMixin
from mails.views import MailFormView


class RegistrationInvitationsView(PaginationMixin, PermissionsMixin, ListView):
    permission_required = "scipost.can_create_registration_invitations"
    queryset = RegistrationInvitation.objects.drafts().not_for_fellows()
    paginate_by = 10
    ordering = ["date_sent_last", "last_name"]
    search_form = None

    def get_queryset(self):
        self.search_form = RegistrationInvitationFilterForm(self.request.GET or None)
        if self.search_form.is_valid():
            self.queryset = self.search_form.search(self.queryset)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count_in_draft"] = RegistrationInvitation.objects.drafts().count()
        context["count_pending"] = RegistrationInvitation.objects.sent().count()
        context[
            "count_unprocessed"
        ] = CitationNotification.objects.unprocessed().count()
        context["search_form"] = self.search_form
        return context


class RegistrationInvitationsSentView(RegistrationInvitationsView):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = RegistrationInvitation.objects.sent().not_for_fellows()
    template_name = "invitations/registrationinvitation_list_sent.html"


class RegistrationInvitationsDraftContributorView(RegistrationInvitationsView):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = RegistrationInvitation.objects.drafts().for_contributors()
    template_name = "invitations/registrationinvitation_list_contributors.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by("created")


class RegistrationInvitationsFellowView(RegistrationInvitationsView):
    permission_required = "scipost.can_invite_fellows"
    queryset = RegistrationInvitation.objects.no_response().for_fellows()
    template_name = "invitations/registrationinvitation_list_fellows.html"


class CitationNotificationsView(PermissionsMixin, PaginationMixin, ListView):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = CitationNotification.objects.unprocessed().prefetch_related(
        "invitation", "contributor", "contributor__user"
    )
    paginate_by = 25


class CitationNotificationsProcessView(
    PermissionsMixin, RequestArgumentMixin, MailFormView
):
    permission_required = "scipost.can_manage_registration_invitations"
    form_class = CitationNotificationProcessForm
    queryset = CitationNotification.objects.unprocessed()
    success_url = reverse_lazy("invitations:citation_notification_list")
    mail_code = "citation_notification"

    def can_send_mail(self):
        """
        Only send mail if Contributor has not opted-out.
        """
        citation = (
            self.get_form()
            .get_all_notifications()
            .filter(contributor__isnull=False)
            .first()
        )
        if not citation.contributor:
            return True
        return citation.contributor.profile.accepts_SciPost_emails

    @transaction.atomic
    def form_valid(self, form):
        """
        Form is valid; the MailFormView will send the mail if
        (possible) Contributor didn't opt-out from mails.
        """
        form.get_all_notifications().update(processed=True)
        return super().form_valid(form)


@login_required
@permission_required(
    "scipost.can_create_registration_invitations", raise_exception=True
)
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
    if request.GET.get("last_name"):
        search_data["last_name"] = request.GET["last_name"]
    if request.GET.get("prefill-last_name"):
        initial_search_data["last_name"] = request.GET["prefill-last_name"]
    suggestion_search_form = SuggestionSearchForm(
        search_data or None, initial=initial_search_data
    )
    if suggestion_search_form.is_valid():
        (
            contributors,
            suggested_invitations,
            declined_invitations,
        ) = suggestion_search_form.search()
    citation_form = CitationNotificationForm(
        request.POST or None,
        contributors=contributors,
        prefix="notification",
        request=request,
    )

    # New citation is related to a Contributor: RegistationInvitation
    invitation_form = RegistrationInvitationForm(
        request.POST or None,
        request=request,
        prefix="invitation",
        initial=initial_search_data,
    )
    if invitation_form.is_valid():
        invitation_form.save()
        messages.success(request, "New Registration Invitation created")
        if request.POST.get("save") == "save_and_create":
            return redirect("invitations:new")
        return redirect("invitations:list")

    # New citation is related to a Contributor: CitationNotification
    if citation_form.is_valid():
        citation_form.save()
        messages.success(request, "New Citation Notification created")
        if request.POST.get("save") == "save_and_create":
            return redirect("invitations:new")
        return redirect("invitations:list")

    context = {
        "suggestion_search_form": suggestion_search_form,
        "citation_form": citation_form,
        "suggested_invitations": suggested_invitations,
        "declined_invitations": declined_invitations,
        "invitation_form": invitation_form,
    }
    return render(
        request, "invitations/registrationinvitation_form_add_new.html", context
    )


class RegistrationInvitationsUpdateView(
    RequestArgumentMixin, PermissionsMixin, MailFormView
):
    permission_required = "scipost.can_create_registration_invitations"
    form_class = RegistrationInvitationForm
    mail_code = "registration_invitation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation_form"] = context["form"]
        return context

    def get_success_url(self):
        if self.request.POST.get("save") == "save_and_create":
            return reverse("invitations:new")
        return reverse("invitations:list")

    def get_queryset(self):
        qs = RegistrationInvitation.objects.drafts()
        if not self.request.user.has_perm("scipost.can_invite_fellows"):
            qs = qs.not_for_fellows()
        if not self.request.user.has_perm(
            "scipost.can_manage_registration_invitations"
        ):
            qs = qs.created_by(self.request.user)
        return qs

    def can_send_mail(self):
        return self.request.user.has_perm("scipost.can_manage_registration_invitations")

    def get_mail_config(self):
        config = super().get_mail_config()
        if self.object.invitation_type == INVITATION_EDITORIAL_FELLOW:
            domain = Site.objects.get_current().domain
            config["from_email"] = f"jscaux@{domain}"
            config["from_name"] = "J-S Caux"
        return config


class RegistrationInvitationsMergeView(
    RequestArgumentMixin, PermissionsMixin, UpdateView
):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = RegistrationInvitation.objects.no_response()
    form_class = RegistrationInvitationMergeForm
    template_name = "invitations/registrationinvitation_form_merge.html"
    success_url = reverse_lazy("invitations:list")


class RegistrationInvitationsAddCitationView(
    RequestArgumentMixin, PermissionsMixin, UpdateView
):
    permission_required = "scipost.can_create_registration_invitations"
    form_class = RegistrationInvitationAddCitationForm
    template_name = "invitations/registrationinvitation_form_add_citation.html"
    success_url = reverse_lazy("invitations:list")
    queryset = RegistrationInvitation.objects.no_response()


class RegistrationInvitationsMarkView(
    RequestArgumentMixin, PermissionsMixin, UpdateView
):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = RegistrationInvitation.objects.drafts()
    form_class = RegistrationInvitationMarkForm
    template_name = "invitations/registrationinvitation_form_mark_as.html"
    success_url = reverse_lazy("invitations:list")


class RegistrationInvitationsMapToContributorView(
    RequestArgumentMixin, PermissionsMixin, UpdateView
):
    permission_required = "scipost.can_manage_registration_invitations"
    model = RegistrationInvitation
    form_class = RegistrationInvitationMapToContributorForm
    template_name = "invitations/registrationinvitation_form_map_to_contributor.html"
    success_url = reverse_lazy("invitations:list")


class RegistrationInvitationsReminderView(
    RequestArgumentMixin, PermissionsMixin, MailFormView
):
    permission_required = "scipost.can_manage_registration_invitations"
    queryset = RegistrationInvitation.objects.sent()
    success_url = reverse_lazy("invitations:list")
    form_class = RegistrationInvitationReminderForm
    template_name = "invitations/registrationinvitation_reminder_form.html"
    mail_code = "registration_invitation_reminder"

    def get_mail_config(self):
        config = super().get_mail_config()
        if self.object.invitation_type == INVITATION_EDITORIAL_FELLOW:
            domain = Site.objects.get_current().domain
            config["from_email"] = f"jscaux@{domain}"
            config["from_name"] = "J-S Caux"
        return config


class RegistrationInvitationsDeleteView(PermissionsMixin, DeleteView):
    permission_required = "scipost.can_manage_registration_invitations"
    model = RegistrationInvitation
    success_url = reverse_lazy("invitations:list")


@login_required
@permission_required(
    "scipost.can_manage_registration_invitations", raise_exception=True
)
def cleanup(request):
    """
    Compares the email addresses of invitations with those in the
    database of registered Contributors. Flags overlaps.
    """
    contributor_email_list = Contributor.objects.values_list("user__email", flat=True)
    invitations = RegistrationInvitation.objects.sent().filter(
        email__in=contributor_email_list
    )
    context = {"invitations": invitations}
    return render(request, "invitations/registrationinvitation_cleanup.html", context)
