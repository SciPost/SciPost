__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.core.handlers.asgi import HttpRequest
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms

from scipost.mixins import PaginationMixin
from organizations.models import Organization

from .models import (
    AffiliateJournal,
    AffiliateJournalYearSubsidy,
    AffiliatePublication,
    AffiliatePubFraction,
)
from .forms import (
    AffiliateJournalAddManagerForm,
    AffiliateJournalForm,
    AffiliateJournalManagerForm,
    AffiliateJournalSpecifyCostInfoForm,
    AffiliateJournalAddPublicationForm,
    AffiliatePublicationAddPubFractionForm,
    AffiliateJournalAddYearSubsidyForm,
)
from .services import get_affiliatejournal_publications_from_Crossref


class AffiliateJournalListView(ListView):
    model = AffiliateJournal


class AffiliateJournalDetailView(DetailView):
    model = AffiliateJournal

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["journal_managers"] = get_users_with_perms(
            self.object, with_superusers=False
        )
        context["add_manager_form"] = AffiliateJournalAddManagerForm()
        context["add_publication_form"] = AffiliateJournalAddPublicationForm(
            initial={"journal": self.object}
        )
        # Get top 5 benefitting Organizations
        pubfractions = AffiliatePubFraction.objects.filter(
            publication__journal=self.object,
        )
        organization_id_list = set(
            [
                p.organization.id
                for p in pubfractions.all().select_related("organization")
            ]
        )
        organizations = Organization.objects.filter(
            id__in=organization_id_list
        ).distinct()
        organizations = organizations.annotate(
            sum_affiliate_pubfractions=Sum(
                "affiliate_pubfractions__fraction",
                filter=Q(affiliate_pubfractions__publication__journal=self.object),
            )
        ).order_by("-sum_affiliate_pubfractions")
        context["top_benefitting_organizations"] = organizations[:10]
        context["specify_cost_info_form"] = AffiliateJournalSpecifyCostInfoForm(
            initial={"journal": self.object}
        )
        context["subsidies_current_year"] = AffiliateJournalYearSubsidy.objects.filter(
            journal=self.object, year=datetime.date.today().year
        )
        return context


class AffiliateJournalUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing affiliate journal.
    """

    model = AffiliateJournal
    template_name = "affiliates/affiliatejournal_form.html"

    def has_permission(self):
        self.object = self.get_object()
        is_journal_manager = self.request.user.has_perm(
            "manage_journal_content", self.object
        )
        return self.request.user.is_staff or is_journal_manager

    def get_form_class(self):
        if self.request.user.is_staff:
            return AffiliateJournalForm
        elif self.request.user.has_perm("manage_journal_content", self.object):
            return AffiliateJournalManagerForm
        return

    def get_success_url(self):
        return reverse("affiliates:journal_detail", kwargs={"slug": self.object.slug})


@permission_required_or_403(
    "affiliates.change_affiliatejournal", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_add_manager(request, slug):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    form = AffiliateJournalAddManagerForm(request.POST or None)
    if form.is_valid():
        assign_perm("manage_journal_content", form.cleaned_data["user"], journal)
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


@permission_required_or_403(
    "affiliates.change_affiliatejournal", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_remove_manager(request, slug, user_id):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    user = get_object_or_404(User, pk=user_id)
    remove_perm("manage_journal_content", user, journal)
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


@permission_required_or_403(
    "affiliates.manage_journal_content", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_specify_cost_info(request, slug):
    form = AffiliateJournalSpecifyCostInfoForm(request.POST or None)
    if form.is_valid():
        form.save()
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


@permission_required_or_403(
    "affiliates.manage_journal_content", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_delete_cost_info(request, slug, year):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    if str(year) in journal.cost_info:
        journal.cost_info.pop(str(year))
        journal.save()
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


@permission_required_or_403(
    "affiliates.manage_journal_content", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_add_publication(request, slug):
    form = AffiliateJournalAddPublicationForm(request.POST or None)
    if form.is_valid():
        form.save()
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


@permission_required_or_403(
    "affiliates.change_affiliatejournal", (AffiliateJournal, "slug", "slug")
)
def affiliatejournal_update_publications_from_Crossref(request, slug):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    total_nr_created = get_affiliatejournal_publications_from_Crossref(journal)
    messages.success(request, "Created %d entries." % total_nr_created)
    return redirect(reverse("affiliates:journal_detail", kwargs={"slug": slug}))


class AffiliatePublicationListView(PaginationMixin, ListView):
    model = AffiliatePublication
    paginate_by = 25

    def get_queryset(self):
        queryset = AffiliatePublication.objects.all()
        if self.request.GET.get("journal", None):
            queryset = queryset.filter(journal__slug=self.request.GET["journal"])
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.GET.get("journal", None):
            context["journal"] = get_object_or_404(
                AffiliateJournal, slug=self.request.GET["journal"]
            )
        return context


class AffiliatePublicationDetailView(DetailView):
    model = AffiliatePublication
    slug_field = "doi"
    slug_url_kwarg = "doi"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["add_pubfraction_form"] = AffiliatePublicationAddPubFractionForm(
            initial={"publication": self.object}
        )
        return context


@permission_required_or_403(
    "affiliates.manage_journal_content", (AffiliateJournal, "slug", "slug")
)
def add_pubfraction(request, slug, doi):
    form = AffiliatePublicationAddPubFractionForm(request.POST or None)
    if form.is_valid():
        form.save()
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("affiliates:publication_detail", kwargs={"doi": doi}))


@permission_required_or_403(
    "affiliates.manage_journal_content", (AffiliateJournal, "slug", "slug")
)
def delete_pubfraction(request, slug, doi, pubfrac_id):
    AffiliatePubFraction.objects.filter(pk=pubfrac_id).delete()
    return redirect(reverse("affiliates:publication_detail", kwargs={"doi": doi}))


class AffiliateJournalOrganizationListView(PaginationMixin, ListView):
    template_name = "affiliates/affiliatejournal_organization_list.html"
    paginate_by = 25

    class Meta:
        model = Organization

    def get_queryset(self):
        # First, get all the relevant AffiliatePubFractions
        journal = get_object_or_404(AffiliateJournal, slug=self.kwargs["slug"])
        pubfractions = AffiliatePubFraction.objects.filter(publication__journal=journal)
        organization_id_list = set(
            [
                p.organization.id
                for p in pubfractions.all().select_related("organization")
            ]
        )
        organizations = Organization.objects.filter(
            id__in=organization_id_list
        ).distinct()
        organizations = organizations.annotate(
            sum_affiliate_pubfractions=Sum(
                "affiliate_pubfractions__fraction",
                filter=Q(affiliate_pubfractions__publication__journal=journal),
            )
        ).order_by("-sum_affiliate_pubfractions")
        return organizations

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["journal"] = get_object_or_404(
            AffiliateJournal, slug=self.kwargs["slug"]
        )
        return context


def affiliatejournal_organization_detail(request, slug, organization_id):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    organization = get_object_or_404(Organization, pk=organization_id)
    affiliatepubfractions = AffiliatePubFraction.objects.filter(
        organization=organization,
        publication__journal=journal,
    ).prefetch_related("publication__journal")
    subsidies = AffiliateJournalYearSubsidy.objects.filter(
        journal=journal,
        organization=organization,
    )
    context = {
        "journal": journal,
        "organization": organization,
        "affiliatepubfractions": affiliatepubfractions,
        "subsidies": subsidies,
        "balance_info": journal.get_balance_info(organization=organization),
    }
    context["balance_cumulative"] = sum(
        [y["balance"] for y in context["balance_info"].values()]
    )
    return render(
        request,
        "affiliates/affiliatejournal_organization_detail.html",
        context,
    )


class AffiliateJournalYearSubsidyListView(PaginationMixin, ListView):
    model = AffiliateJournalYearSubsidy
    template_name = "affiliates/affiliatejournal_subsidy_list.html"
    paginate_by = 25

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["journal"] = get_object_or_404(
            AffiliateJournal, slug=self.kwargs["slug"]
        )
        context["add_subsidy_form"] = AffiliateJournalAddYearSubsidyForm(
            initial={"journal": context["journal"]}
        )
        return context


def journal_add_subsidy(request, slug):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    if not request.user.has_perm("manage_journal_content", journal):
        return HttpResponseForbidden()

    form = AffiliateJournalAddYearSubsidyForm(request.POST or None)
    if form.is_valid():
        form.save()
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("affiliates:journal_subsidies", kwargs={"slug": slug}))


def journal_delete_subsidy(request, slug, pk):
    journal = get_object_or_404(AffiliateJournal, slug=slug)
    if not request.user.has_perm("manage_journal_content", journal):
        return HttpResponseForbidden()

    AffiliateJournalYearSubsidy.objects.filter(pk=pk).delete()
    return redirect(reverse("affiliates:journal_subsidies", kwargs={"slug": slug}))
