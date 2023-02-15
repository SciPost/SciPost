__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from itertools import accumulate
import mimetypes

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

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
from .models import Subsidy, SubsidyAttachment, WorkLog, PeriodicReport
from .utils import slug_to_id

from comments.constants import EXTENTIONS_IMAGES, EXTENTIONS_PDF
from comments.utils import validate_file_extention
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
        (
            pub_data[str(year)]["expenditures"] if str(year) in pub_data else 0
        ) for year in years
    ]
    # only compute balance up to last complete year; set to 0 afterwards
    completed_years = pubyears
    completed_years.pop()
    balance = [
        (subsidies_dict[str(year)] - pub_data[str(year)]["expenditures"]
         if year in completed_years else 0) for year in years
    ]
    # similarly here, put cumulative to zero except for completed years
    cumulative_balance = list(accumulate(balance))
    cumulative_balance = (
        cumulative_balance[:(len(years)-nr_extra_years)] +
        [0]*nr_extra_years
    )
    # matplotlib plot
    width = 0.2
    fig, ax = plt.subplots()
    rects_exp = ax.bar(
        [y - 1.5*width for y in years],
        [e/1000 for e in pub_expenditures],
        width,
        label="Expenditures",
        color="red",
    )
    rects_sub = ax.bar(
        [y - 0.5*width for y in years],
        [s/1000 for s in subsidies],
        width,
        label="Subsidies",
        color="blue",
    )
    rects_bal = ax.bar(
        [y + 0.5*width for y in years],
        [b/1000 for b in balance],
        width,
        label="Balance",
        color="green",
    )
    rects_sub = ax.bar(
        [y + 1.5*width for y in years],
        [c/1000 for c in cumulative_balance],
        width,
        label="Cumulative",
        color="orange",
    )
    ax.legend()
    ax.set_title('Financial balance')
    ax.set_ylabel("\'000 euros")
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
    }
    context["periodic_reports"] = PeriodicReport.objects.all()
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
