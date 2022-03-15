__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from itertools import accumulate
import mimetypes

from csp.decorators import csp_update
from plotly.offline import plot
from plotly.graph_objs import Bar

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .forms import SubsidyForm, SubsidyAttachmentForm, LogsFilterForm
from .models import Subsidy, SubsidyAttachment, WorkLog
from .utils import slug_to_id

from journals.models import Journal, Publication
from organizations.models import Organization
from scipost.mixins import PermissionsMixin


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
        date__year__lte=year, date_until__year__gte=year
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


@csp_update(SCRIPT_SRC=["'unsafe-eval'", "'unsafe-inline'"])
def finances(request):
    now = timezone.now()
    years = [year for year in range(2016, int(now.strftime("%Y")) + 5)]
    subsidies_dict = {}
    for year in years:
        subsidies_dict[str(year)] = total_subsidies_in_year(year)
    subsidies = [subsidies_dict[str(year)] for year in years]
    pub_data = publishing_expenditures()
    pubyears = [year for year in publishing_years()]
    pub_expenditures = [pub_data[str(year)]["expenditures"] for year in pubyears]
    base_expenditures = [-pub_data[str(year)]["expenditures"] for year in pubyears]
    balance = [
        subsidies_dict[str(year)] - pub_data[str(year)]["expenditures"]
        for year in pubyears
    ]
    cumulative_balance = list(accumulate(balance))
    subsidies_plot = plot(
        [
            Bar(
                x=pubyears, y=pub_expenditures, marker_color="red", name="expenditures"
            ),
            Bar(
                x=years, y=subsidies, marker_color="dodgerblue", name="subsidy coverage"
            ),
            Bar(x=pubyears, y=balance, marker_color="indigo", name="balance (year)"),
            Bar(
                x=pubyears,
                y=cumulative_balance,
                marker_color="darkorange",
                name="balance (cumulative)",
            ),
        ],
        config={
            "modeBarButtonsToRemove": [
                "select2d",
                "lasso2d",
                "autoScale2d",
                "toImage",
                "zoom2d",
                "zoomIn2d",
                "zoomOut2d",
            ],
        },
        output_type="div",
        include_plotlyjs=False,
        show_link=False,
        link_text="",
    )
    context = {
        "subsidies_plot": subsidies_plot,
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
    }
    return render(request, "finances/finances.html", context)


def apex(request):
    context = {"data": publishing_expenditures()}
    return render(request, "finances/apex.html", context)


def country_level_data(request):
    context = {}
    context["countrycodes"] = [
        code["country"]
        for code in list(
                Organization.objects.all().distinct("country").values("country")
        )
    ]
    return render(request, "finances/country_level_data.html", context)


def _hx_country_level_data(request, country):
    organizations = Organization.objects.filter(country=country)
    pubyears = [str(y) for y in range(int(timezone.now().strftime("%Y")), 2015, -1)]
    context = {
        "country": country,
        "organizations": organizations,
        "cumulative": {"contribution": 0, "expenditures": 0, "balance": 0},
        "per_year": {}
    }
    for year in pubyears:
        context["per_year"][year] = {
            "contribution": 0,
            "expenditures": 0,
            "balance": 0,
        }
    cumulative_expenditures = 0
    for organization in organizations.all():
        for key in ("contribution", "expenditures", "balance"):
            context["cumulative"][
                key
            ] += organization.cf_balance_info["cumulative"][key]
        for year in pubyears:
            context["per_year"][year]["contribution"] += (
                organization.cf_balance_info[year]["contribution"]
            )
            context["per_year"][year]["expenditures"] += (
                organization.cf_balance_info[year]["expenditures"]["total"]
            )
            context["per_year"][year]["balance"] += (
                organization.cf_balance_info[year]["balance"]
            )
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


class SubsidyListView(ListView):
    model = Subsidy

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.request.GET.get("org")
        if org:
            qs = qs.filter(organization__pk=org)
        order_by = self.request.GET.get("order_by")
        ordering = self.request.GET.get("ordering")
        if order_by == "amount":
            qs = qs.filter(amount_publicly_shown=True).order_by("amount")
        elif order_by == "date":
            qs = qs.order_by("date")
        elif order_by == "until":
            qs = qs.order_by("date_until")
        if ordering == "desc":
            qs = qs.reverse()
        return qs


class SubsidyDetailView(DetailView):
    model = Subsidy


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
        subsidy = get_object_or_404(Subsidy, pk=self.kwargs.get("subsidy_id"))
        return {"subsidy": subsidy}

    def get_success_url(self):
        return reverse_lazy(
            "finances:subsidy_details", kwargs={"pk": self.object.subsidy.id}
        )


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
        return reverse_lazy(
            "finances:subsidy_details", kwargs={"pk": self.object.subsidy.id}
        )


class SubsidyAttachmentDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a SubsidyAttachment.
    """

    permission_required = "scipost.can_manage_subsidies"
    model = SubsidyAttachment

    def get_success_url(self):
        return reverse_lazy(
            "finances:subsidy_details", kwargs={"pk": self.object.subsidy.id}
        )


def subsidy_attachment_toggle_public_visibility(request, attachment_id):
    """
    Method to toggle the public visibility of an attachment to a Subsidy.
    Callable by Admin and Contacts for the relevant Organization.
    """
    attachment = get_object_or_404(SubsidyAttachment, pk=attachment_id)
    if not (
        request.user.has_perm("scipost.can_manage_subsidies")
        or request.user.has_perm(
            "can_view_org_contacts", attachment.subsidy.organization
        )
    ):
        raise PermissionDenied
    attachment.publicly_visible = not attachment.publicly_visible
    attachment.save()
    messages.success(
        request, "Attachment visibility set to %s" % attachment.publicly_visible
    )
    return redirect(attachment.subsidy.get_absolute_url())


def subsidy_attachment(request, subsidy_id, attachment_id):
    attachment = get_object_or_404(
        SubsidyAttachment.objects, subsidy__id=subsidy_id, id=attachment_id
    )
    if not (request.user.is_authenticated and attachment.visible_to_user(request.user)):
        raise PermissionDenied
    content_type, encoding = mimetypes.guess_type(attachment.attachment.path)
    content_type = content_type or "application/octet-stream"
    response = HttpResponse(attachment.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    response["Content-Disposition"] = "filename=%s" % attachment.name
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
