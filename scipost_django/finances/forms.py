__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime
import re

from django import forms
from django.contrib.auth import get_user_model
from django.utils.dates import MONTHS
from django.db.models import Q, Sum
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from crispy_forms.bootstrap import InlineRadios
from crispy_bootstrap5.bootstrap5 import FloatingField

from dal import autocomplete
from dateutil.rrule import rrule, MONTHLY

from organizations.models import Organization
from scipost.fields import UserModelChoiceField

from .models import Subsidy, SubsidyPayment, SubsidyAttachment, WorkLog


class SubsidyForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
    )

    class Meta:
        model = Subsidy
        fields = [
            "organization",
            "subsidy_type",
            "description",
            "amount",
            "amount_publicly_shown",
            "status",
            "paid_on",
            "date_from",
            "date_until",
            "renewable",
            "renewal_of",
        ]


class SubsidySearchForm(forms.Form):
    organization_query = forms.CharField(
        max_length=128,
        required=False,
        label="Organization name or acronym",
    )
    country = forms.CharField(
        max_length=32,
        required=False,
        label="Country name or code",
    )
    ordering = forms.ChoiceField(
        choices=(
            ("amount", "Amount"),
            ("date_from", "Date from"),
            ("date_until", "Date until"),
        ),
        initial="date_from",
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("organization_query"), css_class="col-lg-5"),
                Div(FloatingField("country"), css_class="col-lg-3"),
                Div(InlineRadios("ordering"), css_class="col-lg-4"),
                css_class="row",
            ),
        )

    def search_results(self, user):
        if user.groups.filter(name="Financial Administrators").exists():
            subsidies = Subsidy.objects.all()
        else:
            subsidies = Subsidy.objects.obtained()
        if self.cleaned_data["organization_query"]:
            subsidies = subsidies.filter(
                Q(organization__name__icontains=\
                  self.cleaned_data["organization_query"]) |
                Q(organization__acronym__icontains=\
                  self.cleaned_data["organization_query"])
            )
        if self.cleaned_data["country"]:
            subsidies = subsidies.filter(
                organization__country__icontains=self.cleaned_data["country"],
            )
        if self.cleaned_data["ordering"]:
            if self.cleaned_data["ordering"] == "amount":
                subsidies = subsidies.order_by("-amount")
            if self.cleaned_data["ordering"] == "date_from":
                subsidies = subsidies.order_by("-date_from")
            if self.cleaned_data["ordering"] == "date_until":
                subsidies = subsidies.order_by("-date_until")
        return subsidies


class SubsidyPaymentForm(forms.ModelForm):
    class Meta:
        model = SubsidyPayment
        fields = (
            "subsidy",
            "reference",
            "amount",
            "date_scheduled",
        )


class SubsidyAttachmentForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = (
            "subsidy",
            "attachment",
            "kind",
            "name",
            "date",
            "description",
            "name",
            "visibility",
        )

    def clean_attachment(self):
        attachment = self.cleaned_data["attachment"]
        print(f"{attachment.name = }")
        return attachment

    def clean_name(self):
        name = self.cleaned_data["name"]
        name_regex = (
            "^SciPost_"
            "[0-9]{4,}(-[0-9]{4,})?_[A-Z]{2,}_[\w]+_"
            "(Agreement|Invoice|ProofOfPayment|Other)"
            "(-[0-9]{2,})?\.(pdf|docx|png)$"
        )
        pattern = re.compile(name_regex)
        if not pattern.match(name):
            self.add_error(
                "name",
                "The filename does not match the required regex pattern "
                f"'{name_regex}'"
            )
        return name



#############
# Work logs #
#############


class WorkLogForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.types = kwargs.pop("log_types", False)
        super().__init__(*args, **kwargs)
        if self.types:
            self.fields["log_type"] = forms.ChoiceField(choices=self.types)

    class Meta:
        model = WorkLog
        fields = (
            "comments",
            "log_type",
            "duration",
        )
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 4}),
            "duration": forms.TextInput(attrs={"placeholder": "HH:MM:SS"}),
        }


class LogsFilterForm(forms.Form):
    """
    Filter work logs given the requested date range and users.
    """

    employee = UserModelChoiceField(
        queryset=get_user_model().objects.filter(work_logs__isnull=False).distinct(),
        required=False,
        empty_label="Show all",
    )
    start = forms.DateField(required=True, widget=forms.SelectDateWidget())
    end = forms.DateField(required=True, widget=forms.SelectDateWidget())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.initial["start"] = today.today()
        self.initial["end"] = today.today()

    def clean(self):
        if self.is_valid():
            self.cleaned_data["months"] = [
                dt
                for dt in rrule(
                    MONTHLY,
                    dtstart=self.cleaned_data["start"],
                    until=self.cleaned_data["end"],
                )
            ]
        return self.cleaned_data

    def get_months(self):
        if self.is_valid():
            return self.cleaned_data.get("months", [])
        return []

    def filter(self):
        """Filter work logs and return in user-grouped format."""
        output = []
        if self.is_valid():
            if self.cleaned_data["employee"]:
                user_qs = get_user_model().objects.filter(
                    id=self.cleaned_data["employee"].id
                )
            else:
                user_qs = get_user_model().objects.filter(work_logs__isnull=False)
            user_qs = user_qs.filter(
                work_logs__work_date__gte=self.cleaned_data["start"],
                work_logs__work_date__lte=self.cleaned_data["end"],
            ).distinct()

            output = []
            for user in user_qs:
                logs = user.work_logs.filter(
                    work_date__gte=self.cleaned_data["start"],
                    work_date__lte=self.cleaned_data["end"],
                ).distinct()

                output.append(
                    {
                        "logs": logs,
                        "duration": logs.aggregate(total=Sum("duration")),
                        "user": user,
                    }
                )
        return output

    def filter_per_month(self):
        """Filter work logs and return in per-month format."""
        output = []
        if self.is_valid():
            if self.cleaned_data["employee"]:
                user_qs = get_user_model().objects.filter(
                    id=self.cleaned_data["employee"].id
                )
            else:
                user_qs = get_user_model().objects.filter(work_logs__isnull=False)
            user_qs = user_qs.filter(
                work_logs__work_date__gte=self.cleaned_data["start"],
                work_logs__work_date__lte=self.cleaned_data["end"],
            ).distinct()

            output = []
            for user in user_qs:
                # If logs exists for given filters
                output.append(
                    {
                        "logs": [],
                        "user": user,
                    }
                )
                for dt in self.get_months():
                    output[-1]["logs"].append(
                        user.work_logs.filter(
                            work_date__year=dt.year, work_date__month=dt.month
                        ).aggregate(total=Sum("duration"))["total"]
                    )
        return output
