__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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

from dal import autocomplete

from .models import Funder, Grant
from .forms import (
    FunderRegistrySearchForm,
    FunderForm,
    FunderOrganizationSelectForm,
    GrantForm,
)

from scipost.mixins import PermissionsMixin


class FunderAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        if not self.request.user.has_perm("scipost.can_draft_publication"):
            return None
        qs = Funder.objects.all()
        if self.q:
            qs = qs.filter(
                Q(name__unaccent__icontains=self.q)
                | Q(acronym__unaccent__icontains=self.q)
                | Q(identifier__icontains=self.q)
                | Q(organization__name__unaccent__icontains=self.q)
                | Q(organization__name_original__unaccent__icontains=self.q)
                | Q(organization__acronym__unaccent__icontains=self.q)
            ).order_by("name")
        return qs

    def get_result_label(self, item):
        if item.organization:
            return format_html(
                '<span><i class="{}" title="{}"></i>&emsp;{}</span>',
                item.organization.country.flag_css,
                item.organization.country.name,
                item.name,
            )
        return format_html("<span>{}</span>", item.name)


class GrantAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        if not self.request.user.has_perm("scipost.can_draft_publication"):
            return None
        qs = Grant.objects.all()
        if self.q:
            qs = qs.filter(
                Q(funder__name__unaccent__icontains=self.q)
                | Q(funder__acronym__icontains=self.q)
                | Q(number__icontains=self.q)
                | Q(recipient_name__unaccent__icontains=self.q)
                | Q(recipient__user__last_name__unaccent__icontains=self.q)
                | Q(recipient__user__first_name__unaccent__icontains=self.q)
                | Q(further_details__icontains=self.q)
            ).order_by("funder__name", "number")
        return qs

    def get_result_label(self, item):
        return format_html(
            "<span>Number:&nbsp;{}<br>Recipient:&nbsp;{}<br>From:&nbsp;{}",
            item.number,
            item.recipient if item.recipient else item.recipient_name,
            item.funder,
        )


@permission_required("scipost.can_view_all_funding_info", raise_exception=True)
def funders_dashboard(request):
    """Administration of Funders and Grants."""
    funders = Funder.objects.all()
    form = FunderRegistrySearchForm()
    grants = Grant.objects.all()
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
