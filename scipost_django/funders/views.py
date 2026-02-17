__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.views.generic import DeleteView, DetailView, ListView
import requests
import json

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import get_object_or_404, render, redirect

from common.views import HXDynselAutocomplete

from .models import Funder, Grant, IndividualBudget
from .forms import (
    FunderRegistrySearchForm,
    FunderForm,
    FunderOrganizationSelectForm,
    GrantForm,
    IndividualBudgetForm,
)

from scipost.mixins import PermissionsMixin


class HXDynselFunderAutocomplete(HXDynselAutocomplete):
    model = Funder

    def search(self, queryset, q):
        return queryset.filter(
            Q(name__unaccent__icontains=q)
            | Q(acronym__unaccent__icontains=q)
            | Q(identifier__icontains=q)
            | Q(organization__name__unaccent__icontains=q)
            | Q(organization__name_original__unaccent__icontains=q)
            | Q(organization__acronym__unaccent__icontains=q)
        ).order_by("name")


class HXDynselGrantAutocomplete(HXDynselAutocomplete):
    model = Grant

    def search(self, queryset, q):
        if not self.request.user.has_perm("scipost.can_draft_publication"):
            return Grant.objects.none()
        else:
            return queryset.filter(
                Q(funder__name__unaccent__icontains=q)
                | Q(funder__acronym__icontains=q)
                | Q(number__icontains=q)
                | Q(recipient_name__unaccent__icontains=q)
                | Q(recipient__dbuser__last_name__unaccent__icontains=q)
                | Q(recipient__dbuser__first_name__unaccent__icontains=q)
                | Q(further_details__icontains=q)
            ).order_by("funder__name", "number")


@permission_required("scipost.can_view_all_funding_info", raise_exception=True)
def funders_dashboard(request):
    """Administration of Funders and Grants."""
    funders = Funder.objects.all().select_related("organization")
    form = FunderRegistrySearchForm()
    grants = (
        Grant.objects.all()
        .select_related("funder", "recipient__profile")
        .order_by("funder__name", "number")
    )
    grant_form = GrantForm(request=request)
    context = {
        "form": form,
        "funders": funders,
        "grants": grants,
        "grant_form": grant_form,
    }
    return render(request, "funders/funders_dashboard.html", context)


@permission_required("scipost.can_view_all_funding_info", raise_exception=True)
def query_crossref_for_funder(request):
    """
    Checks Crossref's Fundref Registry for an entry
    corresponding to the funder name being looked for.
    If found, creates a funders.Funder instance.
    """
    form = FunderRegistrySearchForm(request.POST or None)
    context = {"form": form}
    if form.is_valid():
        queryurl = (
            "http://api.crossref.org/funders?query=%s" % form.cleaned_data["name"]
        )
        query = requests.get(queryurl)
        response = json.loads(query.text)
        context["response_headers"] = query.headers
        context["response_text"] = query.text
        context["response"] = response
        context["funder_form"] = FunderForm()
    return render(request, "funders/query_crossref_for_funder.html", context)


@permission_required("scipost.can_view_all_funding_info", raise_exception=True)
def add_funder(request):
    form = FunderForm(request.POST or None)
    if form.is_valid():
        funder = form.save()
        messages.success(
            request, ("<h3>Funder %s successfully created</h3>") % str(funder)
        )
    elif form.has_changed():
        messages.warning(request, "The form was invalidly filled.")
    return redirect(reverse("funders:funders_dashboard"))


def funders(request):
    """List page of Funders."""
    funders = Funder.objects.has_publications().distinct()
    context = {"funders": funders}
    return render(request, "funders/funder_list.html", context)


def funder_publications(request, funder_id):
    """Detail page of a specific Funder (publicly accessible)."""
    funder = get_object_or_404(Funder, id=funder_id)
    context = {"funder": funder}
    return render(request, "funders/funder_details.html", context)


class HttpRefererMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data.get("http_referer"):
            self.success_url = form.cleaned_data["http_referer"]
        return super().form_valid(form)


class LinkFunderToOrganizationView(PermissionsMixin, UpdateView):
    """
    For an existing Funder instance, specify the link to an Organization.
    """

    permission_required = "scipost.can_create_grants"
    model = Funder
    form_class = FunderOrganizationSelectForm
    template_name = "funders/funder_link_organization.html"
    success_url = reverse_lazy("funders:funders_dashboard")

    def form_valid(self, form):
        form.instance.organization = form.cleaned_data["organization"]
        return super().form_valid(form)


@method_decorator(transaction.atomic, name="dispatch")
class CreateGrantView(PermissionsMixin, HttpRefererMixin, CreateView):
    """
    Create a Grant in a separate window which may also be used by Production Supervisors.
    """

    permission_required = "scipost.can_create_grants"
    model = Grant
    form_class = GrantForm
    success_url = reverse_lazy("funders:funders_dashboard")


#######################
# Individual Budgets #
#######################


class IndividualBudgetListView(PermissionsMixin, ListView):
    model = IndividualBudget
    template_name = "funders/individual_budget_list.html"
    permission_required = "scipost.can_manage_subsidies"
    context_object_name = "budgets"


class IndividualBudgetDetailView(PermissionsMixin, DetailView):
    model = IndividualBudget
    template_name = "funders/individual_budget_detail.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "budget_id"
    context_object_name = "budget"


class IndividualBudgetDeleteView(PermissionsMixin, DeleteView):
    model = IndividualBudget
    template_name = "funders/individual_budget_delete.html"
    success_url = reverse_lazy("finances:subsidies")
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "budget_id"
    context_object_name = "budget"


class IndividualBudgetCreateView(PermissionsMixin, CreateView):
    model = IndividualBudget
    form_class = IndividualBudgetForm
    template_name = "funders/individual_budget_form.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "budget_id"
    context_object_name = "budget"


class IndividualBudgetUpdateView(PermissionsMixin, UpdateView):
    model = IndividualBudget
    form_class = IndividualBudgetForm
    template_name = "funders/individual_budget_form.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "budget_id"
    context_object_name = "budget"
