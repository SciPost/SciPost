__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from itertools import accumulate, chain
import mimetypes
from typing import Any
from dal import autocomplete

from django.contrib.contenttypes.models import ContentType
from django.core.handlers.asgi import HttpRequest
from django.db import models
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.views.generic import FormView
import matplotlib

from common.views import HXDynselAutocomplete, HXDynselSelectOptionView
from finances.constants import SUBSIDY_TYPE_SPONSORSHIPAGREEMENT, SUBSIDY_PROMISED
from finances.models.account import Account
from finances.models.subsidy import SubsidyCollective
from journals.models.publication import PublicationAuthorsTable

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .forms import (
    SubsidyAttachmentInlineLinkForm,
    SubsidyAttachmentSearchForm,
    SubsidyCollectiveForm,
    SubsidyCollectiveRenewForm,
    SubsidyForm,
    SubsidySearchForm,
    SubsidyPaymentForm,
    SubsidyAttachmentForm,
    LogsFilterForm,
)
from .models import Subsidy, SubsidyPayment, SubsidyAttachment, WorkLog, PeriodicReport
from .utils import slug_to_id

from comments.constants import EXTENTIONS_IMAGES, EXTENTIONS_PDF
from comments.utils import validate_file_extention
from journals.models import Journal, Publication
from organizations.models import Organization
from scipost.mixins import PermissionsMixin
from scipost.permissions import HTMXPermissionsDenied, HTMXResponse
from pins.models import Note


# TODO: Why is this a context preprocesor? Refactor it.
def publishing_years():
    start_year = (
        Publication.objects.all()
        .order_by("publication_date")
        .first()
        .publication_date.strftime("%Y")
    )
    return range(int(start_year), int(timezone.now().strftime("%Y")) + 1)


def total_subsidies_in_year(year):
    total = 0
    for subsidy in Subsidy.objects.filter(
        date_from__year__lte=year, date_until__year__gte=year
    ):
        total += subsidy.value_in_year(year)
    return total


def publishing_expenditures():
    pubyears = publishing_years()
    journals = Journal.objects.all()
    data = {"pubyears": pubyears}
    for year in pubyears:
        data[str(year)] = {}
        year_expenditures = 0
        for journal in journals:
            npub = (
                journal.get_publications().filter(publication_date__year=year).count()
            )
            expenditures = npub * journal.cost_per_publication(year)
            data[str(year)][journal.doi_label] = {
                "npub": npub,
                "cost_per_pub": journal.cost_per_publication(year),
                "expenditures": expenditures,
            }
            year_expenditures += expenditures
        data[str(year)]["expenditures"] = year_expenditures
    return data


def recent_publishing_expenditures(months=6):
    """
    Tally of total publishing expenditures over last `months` number of months.
    """
    deltat = datetime.timedelta(days=months * 30)
    npub_total = 0
    expenditures = 0
    for journal in Journal.objects.all():
        npub = (
            journal.get_publications()
            .filter(publication_date__gte=timezone.now() - deltat)
            .count()
        )
        npub_total += npub
        expenditures += npub * journal.cost_per_publication(
            timezone.now().strftime("%Y")
        )
    return {"npub": npub_total, "expenditures": expenditures}


def finances(request):
    now = timezone.now()
    # for plotting up to last completed year: put nr_extra_years to 0;
    # to plot in future (to see e.g. future subsidy coverage), add more
    nr_extra_years = 5
    years = [year for year in range(2016, int(now.strftime("%Y")) + nr_extra_years)]
    subsidies_dict = {}
    for year in years:
        subsidies_dict[str(year)] = total_subsidies_in_year(year)
    subsidies = [subsidies_dict[str(year)] for year in years]
    pub_data = publishing_expenditures()
    pubyears = [year for year in publishing_years()]
    pub_expenditures = [
        (pub_data[str(year)]["expenditures"] if str(year) in pub_data else 0)
        for year in years
    ]
    # only compute balance up to last complete year; set to 0 afterwards
    completed_years = pubyears
    completed_years.pop()
    balance = [
        (
            subsidies_dict[str(year)] - pub_data[str(year)]["expenditures"]
            if year in completed_years
            else 0
        )
        for year in years
    ]
    # similarly here, put cumulative to zero except for completed years
    cumulative_balance = list(accumulate(balance))
    cumulative_balance = (
        cumulative_balance[: (len(years) - nr_extra_years)] + [0] * nr_extra_years
    )
    # matplotlib plot
    width = 0.2
    fig, ax = plt.subplots()
    rects_exp = ax.bar(
        [y - 1.5 * width for y in years],
        [e / 1000 for e in pub_expenditures],
        width,
        label="Expenditures",
        color="red",
    )
    rects_sub = ax.bar(
        [y - 0.5 * width for y in years],
        [s / 1000 for s in subsidies],
        width,
        label="Subsidies",
        color="blue",
    )
    rects_bal = ax.bar(
        [y + 0.5 * width for y in years],
        [b / 1000 for b in balance],
        width,
        label="Balance",
        color="green",
    )
    rects_sub = ax.bar(
        [y + 1.5 * width for y in years],
        [c / 1000 for c in cumulative_balance],
        width,
        label="Cumulative",
        color="orange",
    )
    ax.legend()
    ax.set_title("Financial balance")
    ax.set_ylabel("'000 euros")
    ax.set_xlabel("year")

    flike = io.BytesIO()
    fig.savefig(flike)
    subsidies_plot_b64 = base64.b64encode(flike.getvalue()).decode()
    context = {
        "subsidies_plot": subsidies_plot_b64,
    }
    current_year = int(now.strftime("%Y"))
    future_subsidies = 0
    for key, val in subsidies_dict.items():
        if int(key) > current_year:
            future_subsidies += val
    resources = cumulative_balance[-1] + future_subsidies
    recent_exp = recent_publishing_expenditures(6)
    context["resources"] = {
        "resources": resources,
        "expenditures_mo": recent_exp["expenditures"] / 6,
        "sustainable_months": resources * 6 / recent_exp["expenditures"],
        "npub": recent_exp["npub"] * resources / recent_exp["expenditures"],
        "sustainable_until": now
        + datetime.timedelta(days=30.5 * resources * 6 / recent_exp["expenditures"]),
        "liquidities": Account.objects.all().first().balance.amount,
        "account_zero_date": Account.objects.all().first().zero_balance_projection,
    }
    context["periodic_reports"] = PeriodicReport.objects.all()

    return render(request, "finances/finances.html", context)


def apex(request):
    context = {"data": publishing_expenditures()}
    return render(request, "finances/apex.html", context)


def country_level_data(request):
    context = {}
    countrycodes = [
        code["country"]
        for code in list(
            Organization.objects.all().distinct("country").values("country")
        )
    ]
    context = {
        "countrycodes": countrycodes,
    }
    countrydatalist = []
    for country in countrycodes:
        country_organizations = Organization.objects.filter(country=country)
        countrydata = {
            "country": country,
            "expenditures": 0,
            "expenditures_rank": None,
            "subsidy_income": 0,
            "subsidy_income_rank": None,
            "impact_on_reserves": 0,
            "impact_on_reserves_rank": None,
        }
        for organization in country_organizations:
            for key in ("subsidy_income", "expenditures", "impact_on_reserves"):
                countrydata[key] += organization.cf_balance_info["cumulative"][key]
        countrydatalist += [
            countrydata,
        ]

    # Determine the ranks
    countrydatalist.sort(key=lambda country: country["expenditures"], reverse=True)
    for idx, c in enumerate(countrydatalist):
        c["expenditures_rank"] = idx + 1
    countrydatalist.sort(key=lambda country: country["subsidy_income"], reverse=True)
    for idx, c in enumerate(countrydatalist):
        c["subsidy_income_rank"] = idx + 1
    countrydatalist.sort(
        key=lambda country: country["impact_on_reserves"], reverse=True
    )
    for idx, c in enumerate(countrydatalist):
        c["impact_on_reserves_rank"] = idx + 1
    ordering = request.GET.get("ordering", None)
    reverse_ordering = request.GET.get("reverse", None)
    if ordering == "expenditures":
        countrydatalist.sort(key=lambda country: country["expenditures"])
    elif ordering == "subsidy_income":
        countrydatalist.sort(key=lambda country: country["subsidy_income"])
    elif ordering == "impact":
        countrydatalist.sort(key=lambda country: country["impact_on_reserves"])
    if reverse_ordering == "true":
        countrydatalist.reverse()

    context["countrydata"] = countrydatalist
    return render(request, "finances/country_level_data.html", context)


def _hx_country_level_data(request, country):
    organizations = Organization.objects.filter(country=country)
    pubyears = [str(y) for y in range(int(timezone.now().strftime("%Y")), 2015, -1)]
    context = {
        "country": country,
        "organizations": organizations,
        "cumulative": {
            "subsidy_income": 0,
            "expenditures": 0,
            "impact_on_reserves": 0,
            "nap": len(
                set(chain.from_iterable([o.get_publications() for o in organizations]))
            ),
        },
        "per_year": {},
    }

    def get_yearly_nap_of_country(country: str) -> dict[int, int]:
        return dict(
            Publication.objects.annotate(
                has_author_of_country=Exists(
                    PublicationAuthorsTable.objects.filter(
                        publication=OuterRef("pk"), affiliations__country=country
                    )
                )
            )
            .filter(has_author_of_country=True)
            .values("publication_date__year")
            .annotate(nr=Count("publication_date__year"))
            .order_by("publication_date__year")
            .values_list("publication_date__year", "nr")
        )

    country_yearly_nap = get_yearly_nap_of_country(country)
    for year in pubyears:
        context["per_year"][year] = {
            "subsidy_income": 0,
            "expenditures": 0,
            "impact_on_reserves": 0,
            "nap": country_yearly_nap.get(int(year), 0),
        }
    for organization in organizations.all():
        for key in ("subsidy_income", "expenditures", "impact_on_reserves"):
            context["cumulative"][key] += organization.cf_balance_info["cumulative"][
                key
            ]
        for year in pubyears:
            context["per_year"][year]["subsidy_income"] += organization.cf_balance_info[
                year
            ]["subsidy_income"]
            context["per_year"][year]["expenditures"] += organization.cf_balance_info[
                year
            ]["expenditures"]["total"]["expenditures"]
            context["per_year"][year][
                "impact_on_reserves"
            ] += organization.cf_balance_info[year]["impact_on_reserves"]
    return render(request, "finances/_hx_country_level_data.html", context)


#############
# Subsidies #
#############


class SubsidyCreateView(PermissionsMixin, CreateView):
    """
    Create a new Subsidy.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = Subsidy
    form_class = SubsidyForm
    template_name = "finances/subsidy_form.html"

    def get_success_url(self):
        return reverse_lazy("finances:subsidy_details", kwargs={"pk": self.object.id})


class SubsidyUpdateView(PermissionsMixin, UpdateView):
    """
    Update a Subsidy.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = Subsidy
    form_class = SubsidyForm
    template_name = "finances/subsidy_form.html"

    def get_success_url(self):
        return reverse_lazy("finances:subsidy_details", kwargs={"pk": self.object.id})


class SubsidyDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Subsidy.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = Subsidy
    success_url = reverse_lazy("finances:subsidies")


class SubsidyAutocompleteView(autocomplete.Select2QuerySetView):
    """
    Autocomplete for Subsidy, meant to be used with Select2.
    Will only show subsidies whose amounts are publicly visible
    for users without the 'can_manage_subsidies' permission.
    """

    def get_queryset(self):
        qs = Subsidy.objects.all()
        if not self.request.user.has_perm("scipost.can_manage_subsidies"):
            qs = qs.filter(amount_publicly_shown=True)
        if self.q:
            qs = qs.filter(
                Q(organization__name__unaccent__icontains=self.q)
                | Q(organization__name_original__unaccent__icontains=self.q)
                | Q(organization__acronym__unaccent__icontains=self.q)
                | Q(amount__icontains=self.q)
                | Q(description__icontains=self.q)
                | Q(date_from__year__icontains=self.q)
                | Q(date_until__year__icontains=self.q)
            )
        return qs

    def get_result_label(self, item):
        return format_html(
            "{}<br>{} -> {} [{}]",
            item.organization.name,
            item.date_from,
            item.date_until,
            item.get_status_display(),
        )


class SubsidyListView(ListView):
    model = Subsidy
    template_name = "finances/subsidy_list_old.html"

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.request.GET.get("org")
        if org:
            qs = qs.filter(organization__pk=org)
        order_by = self.request.GET.get("order_by")
        ordering = self.request.GET.get("ordering")
        if order_by == "amount":
            qs = qs.filter(amount_publicly_shown=True).order_by("amount")
        elif order_by == "date_from":
            qs = qs.order_by("date_from")
        elif order_by == "date_until":
            qs = qs.order_by("date_until")
        if ordering == "desc":
            qs = qs.reverse()
        return qs.select_related("organization").prefetch_related(
            "attachments",
            "renewal_of__organization",
            "renewed_by__organization",
        )


class SubsidyDetailView(DetailView):
    model = Subsidy


class OrganizationSponsorshipSubsidyCreateView(PermissionsMixin, CreateView):
    """
    Create a new Subsidy as a sponsorship from an Organization.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = Subsidy
    form_class = SubsidyForm
    template_name = "finances/subsidy_form.html"

    def get_initial(self):
        organization = get_object_or_404(
            Organization, pk=self.kwargs.get("organization_id")
        )
        last_subsidy = Subsidy.objects.filter(organization=organization).first()
        current_year = timezone.now().year
        return {
            "organization": organization,
            "subsidy_type": SUBSIDY_TYPE_SPONSORSHIPAGREEMENT,
            "status": SUBSIDY_PROMISED,
            "renewable": True,
            "amount": last_subsidy.amount if last_subsidy else None,
            "renewal_of": last_subsidy,
            "date_from": datetime.date(current_year, 1, 1),
            "date_until": datetime.date(current_year, 12, 31),
        }

    def get_success_url(self):
        return reverse_lazy("finances:subsidy_details", kwargs={"pk": self.object.id})


def subsidy_list(request):
    initial = {}
    org_id_str = str(request.GET.get("org", ""))
    if (
        org_id_str.isdigit()
        and (org_id := int(org_id_str))
        and (org := Organization.objects.filter(pk=org_id).first())
    ):
        initial["organization_query"] = org.name
    form = SubsidySearchForm(initial=initial)
    context = {
        "form": form,
    }
    return render(request, "finances/subsidy_list.html", context)


def _hx_subsidy_list(request):
    form = SubsidySearchForm(request.POST or None)
    if form.is_valid():
        subsidies = form.search_results(request.user)
    else:
        subsidies = Subsidy.objects.all()

    content_type = ContentType.objects.get_for_model(Subsidy)
    subsidies = subsidies.annotate(
        nr_visible_notes=Coalesce(
            Subquery(
                Note.objects.visible_for(request.user, content_type.id, OuterRef("id"))
                .values("regarding_object_id")
                .annotate(nr=Count("id"))
                .values("nr"),
                output_field=models.IntegerField(),
            ),
            0,
        )
    )

    paginator = Paginator(subsidies, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "form": form,
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "finances/_hx_subsidy_list.html", context)


@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def allocate_subsidy(request, subsidy_id: int):
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    subsidy.allocate()
    return redirect(reverse("finances:subsidy_details", kwargs={"pk": subsidy.id}))


@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def _hx_subsidy_finadmin_details(request, subsidy_id: int):
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    if not (
        request.user.has_perm("scipost.can_manage_subsidies")
        or request.user.has_perm("can_view_org_contacts", subsidy.organization)
    ):
        raise PermissionDenied
    context = {
        "subsidy": subsidy,
    }
    return render(request, "finances/_hx_subsidy_finadmin_details.html", context)


@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def _hx_subsidypayment_button(request, subsidy_id: int):
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    return render(
        request,
        "finances/_hx_subsidypayment_button.html",
        context={
            "subsidy": subsidy,
        },
    )


@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def _hx_subsidypayment_form(request, subsidy_id: int, subsidypayment_id: int = None):
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    if subsidypayment_id:
        instance = get_object_or_404(SubsidyPayment, pk=subsidypayment_id)
    else:
        instance = None
    form = SubsidyPaymentForm(
        request.POST or None,
        subsidy=subsidy,
        instance=instance,
    )
    if form.is_valid():
        form.save()
        response = render(
            request,
            "finances/_hx_subsidy_finadmin_details.html",
            context={
                "subsidy": subsidy,
            },
        )
        response["HX-Retarget"] = f"#subsidy-{subsidy.id}-finadmin-details"
        return response
    context = {
        "subsidy": subsidy,
        "form": form,
    }
    return render(request, "finances/_hx_subsidypayment_form.html", context)


@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def _hx_subsidypayment_delete(request, subsidy_id: int, subsidypayment_id: int):
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    SubsidyPayment.objects.filter(pk=subsidypayment_id).delete()
    response = render(
        request,
        "finances/_hx_subsidy_finadmin_details.html",
        context={
            "subsidy": subsidy,
        },
    )
    return response


def subsidy_toggle_amount_public_visibility(request, subsidy_id):
    """
    Method to toggle the public visibility of the amount of a Subsidy.
    Callable by Admin and Contacts for the relevant Organization.
    """
    subsidy = get_object_or_404(Subsidy, pk=subsidy_id)
    if not (
        request.user.has_perm("scipost.can_manage_subsidies")
        or request.user.has_perm("can_view_org_contacts", subsidy.organization)
    ):
        raise PermissionDenied
    subsidy.amount_publicly_shown = not subsidy.amount_publicly_shown
    subsidy.save()
    messages.success(
        request, "Amount visibility set to %s" % subsidy.amount_publicly_shown
    )
    return redirect(subsidy.get_absolute_url())


class SubsidyAttachmentCreateView(PermissionsMixin, CreateView):
    """
    Create a new SubsidyAttachment.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = SubsidyAttachment
    form_class = SubsidyAttachmentForm
    template_name = "finances/subsidyattachment_form.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["countrycodes"] = [
            code["country"]
            for code in list(
                Organization.objects.all().distinct("country").values("country")
            )
        ]
        return context

    def get_initial(self):
        subsidy_id = self.kwargs.get("subsidy_id")
        if subsidy_id is not None:
            subsidy = get_object_or_404(Subsidy, pk=self.kwargs.get("subsidy_id"))
            return {"subsidy": subsidy}
        return {}

    def get_success_url(self):
        if subsidy := self.object.subsidy:
            return reverse_lazy("finances:subsidy_details", kwargs={"pk": subsidy.id})

        return reverse_lazy("finances:subsidies")


class SubsidyAttachmentUpdateView(PermissionsMixin, UpdateView):
    """
    Update a SubsidyAttachment.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = SubsidyAttachment
    form_class = SubsidyAttachmentForm
    template_name = "finances/subsidyattachment_form.html"
    success_url = reverse_lazy("finances:subsidies")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["countrycodes"] = [
            code["country"]
            for code in list(
                Organization.objects.all().distinct("country").values("country")
            )
        ]
        return context

    def get_success_url(self):
        if subsidy := self.object.subsidy:
            return reverse_lazy("finances:subsidy_details", kwargs={"pk": subsidy.id})

        return reverse_lazy("finances:subsidies")


class SubsidyAttachmentDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a SubsidyAttachment.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = SubsidyAttachment

    def get_success_url(self):
        if subsidy := self.object.subsidy:
            return reverse_lazy("finances:subsidy_details", kwargs={"pk": subsidy.id})

        return reverse_lazy("finances:subsidies")


@login_required()
@permission_required("scipost.can_manage_subsidies", raise_exception=True)
def subsidyattachment_orphaned_list(request):
    nr_orphaned_subsidies = SubsidyAttachment.objects.orphaned().count()
    return TemplateResponse(
        request,
        "finances/subsidyattachment_orphaned_list.html",
        {
            "nr_orphaned_subsidies": nr_orphaned_subsidies,
        },
    )


def _hx_subsidyattachment_search_form(request, filter_set: str):
    form = SubsidyAttachmentSearchForm(
        user=request.user,
        session_key=request.session.session_key,
    )

    if filter_set == "empty":
        form.apply_filter_set({}, none_on_empty=True)

    context = {
        "form": form,
    }
    return render(request, "finances/_hx_subsidyattachment_search_form.html", context)


def _hx_subsidyattachment_list_page(request):
    form = SubsidyAttachmentSearchForm(
        request.POST or None, user=request.user, session_key=request.session.session_key
    )
    if form.is_valid():
        attachments = form.search_results()
    else:
        attachments = SubsidyAttachment.objects.orphaned()
    paginator = Paginator(attachments, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index

    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
        "form_media": SubsidyAttachmentForm().media,
    }
    return render(request, "finances/_hx_subsidyattachment_list_page.html", context)


def _hx_subsidyattachment_link_form(request, attachment_id):
    attachment = get_object_or_404(SubsidyAttachment, pk=attachment_id)
    subsidy_id = request.POST.get("subsidy", None)
    subsidy = Subsidy.objects.get(pk=subsidy_id) if subsidy_id else None
    subsidy_payment_id = request.POST.get("subsidy_payment", None)
    subsidy_payment = (
        SubsidyPayment.objects.get(pk=subsidy_payment_id)
        if subsidy_payment_id
        else None
    )
    form = SubsidyAttachmentInlineLinkForm(
        request.POST or None,
        instance=attachment,
        initial={
            "subsidy": subsidy or getattr(attachment, "subsidy", None),
            "subsidy_payment": subsidy_payment,
        },
    )
    if form.is_valid():
        form.save()

    context = {
        "attachment": attachment,
        "form": form,
    }
    return TemplateResponse(
        request, "finances/_hx_subsidyattachment_link_form.html", context
    )


class HXDynselSubsidyAutocomplete(HXDynselAutocomplete):
    model = Subsidy

    def search(self, queryset, q):
        return queryset.filter(
            Q(organization__name__unaccent__icontains=q)
            | Q(organization__name_original__unaccent__icontains=q)
            | Q(organization__acronym__unaccent__icontains=q)
            | Q(amount__icontains=q)
            | Q(description__icontains=q)
            | Q(date_from__year__icontains=q)
            | Q(date_until__year__icontains=q)
        )


def subsidy_attachment(request, attachment_id):
    attachment = get_object_or_404(SubsidyAttachment.objects, id=attachment_id)
    if not (request.user.is_authenticated and attachment.visible_to_user(request.user)):
        raise PermissionDenied
    content_type, encoding = mimetypes.guess_type(attachment.attachment.path)
    content_type = content_type or "application/octet-stream"
    response = HttpResponse(attachment.attachment.read(), content_type=content_type)
    if encoding:
        response["Content-Encoding"] = encoding
        response["Content-Disposition"] = "filename=%s" % attachment.attachment.name
    return response


############################
# Timesheets and Work Logs #
############################


@permission_required("scipost.can_view_timesheets", raise_exception=True)
def timesheets(request):
    """
    Overview of all timesheets including comments and related objects.
    """
    form = LogsFilterForm(request.GET or None)
    context = {"form": form}
    return render(request, "finances/timesheets.html", context)


@permission_required("scipost.can_view_timesheets", raise_exception=True)
def timesheets_detailed(request):
    """Overview of all timesheets."""
    form = LogsFilterForm(request.GET or None)
    context = {"form": form}
    return render(request, "finances/timesheets_detailed.html", context)


class LogDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkLog

    def get_object(self):
        try:
            return WorkLog.objects.get(
                user=self.request.user, id=slug_to_id(self.kwargs["slug"])
            )
        except WorkLog.DoesNotExist:
            raise Http404

    def get_success_url(self):
        messages.success(self.request, "Log deleted.")
        return self.object.content.get_absolute_url()


@permission_required("scipost.can_view_production", raise_exception=True)
def _hx_worklog_delete(request, slug):
    log = get_object_or_404(WorkLog, pk=slug_to_id(slug))

    if request.user != log.user:
        return HTMXPermissionsDenied(
            "You do not have permission to delete this work log."
        )

    log.delete()

    return HTMXResponse("Work log has been deleted.", tag="danger")


def personal_timesheet(request):
    """
    Overview of the user's timesheets across all production streams.
    """
    return render(request, "finances/personal_timesheet.html")


###################
# PeriodicReports #
###################


def periodicreport_file(request, pk):
    periodicreport = get_object_or_404(PeriodicReport, pk=pk)
    if validate_file_extention(periodicreport._file, EXTENTIONS_IMAGES):
        content_type = "image/jpeg"
    elif validate_file_extention(periodicreport._file, EXTENTIONS_PDF):
        content_type = "application/pdf"
    else:
        raise Http404
    response = HttpResponse(periodicreport._file.read(), content_type=content_type)
    filename = periodicreport._file.name
    response["Content-Disposition"] = f"filename={filename}"
    return response


#######################
# Subsidy Collectives #
#######################


class SubsidyCollectiveListView(PermissionsMixin, ListView):
    model = SubsidyCollective
    template_name = "finances/subsidy_collective_list.html"
    permission_required = "scipost.can_manage_subsidies"
    context_object_name = "collectives"


class SubsidyCollectiveDetailView(PermissionsMixin, DetailView):
    model = SubsidyCollective
    template_name = "finances/subsidy_collective_detail.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_encapsulated_subsidies"] = Paginator(
            self.object.subsidies.all(),
            1000,
        ).get_page(self.request.GET.get("page"))
        return context


class SubsidyCollectiveDeleteView(PermissionsMixin, DeleteView):
    model = SubsidyCollective
    template_name = "finances/subsidy_collective_delete.html"
    success_url = reverse_lazy("finances:subsidy_collectives")
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"


class SubsidyCollectiveCreateView(PermissionsMixin, CreateView):
    model = SubsidyCollective
    form_class = SubsidyCollectiveForm
    template_name = "finances/subsidy_collective_form.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_success_url(self):
        return self.object.get_absolute_url()


class SubsidyCollectiveUpdateView(PermissionsMixin, UpdateView):
    model = SubsidyCollective
    form_class = SubsidyCollectiveForm
    template_name = "finances/subsidy_collective_form.html"
    permission_required = "scipost.can_manage_subsidies"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_success_url(self):
        return self.object.get_absolute_url()


class SubsidyCollectiveRenewFormView(FormView):
    template_name = "finances/subsidy_collective_renew_form.html"
    form_class = SubsidyCollectiveRenewForm

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        self.collective = get_object_or_404(
            SubsidyCollective, pk=kwargs.get("collective_id", None)
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["collective"] = self.collective
        return kwargs

    def get_initial(self):
        return {"collective": self.collective}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collective"] = self.collective
        return context

    def get_success_url(self):
        return self.new_collective.get_absolute_url()

    def form_valid(self, form):
        self.new_collective = form.save()
        return super().form_valid(form)
