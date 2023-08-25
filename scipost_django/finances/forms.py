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
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
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
        widgets = {
            "paid_on": forms.DateInput(attrs={"type": "date"}),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_until": forms.DateInput(attrs={"type": "date"}),
        }


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
        if organization_query := self.cleaned_data["organization_query"]:
            subsidies = subsidies.filter(
                Q(organization__name__unaccent__icontains=organization_query)
                | Q(organization__acronym__unaccent__icontains=organization_query)
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
            "invoice",
            "proof_of_payment",
        )
        widgets = {
            "date_scheduled": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        subsidy = kwargs.pop("subsidy")
        super().__init__(*args, **kwargs)
        self.fields["subsidy"].initial = subsidy
        self.fields["subsidy"].widget = forms.HiddenInput()
        self.fields["invoice"].queryset = subsidy.attachments.invoices()
        self.fields[
            "proof_of_payment"
        ].queryset = subsidy.attachments.proofs_of_payment()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("subsidy"),
            Div(
                Div(FloatingField("reference"), css_class="col-lg-5"),
                Div(FloatingField("amount"), css_class="col-lg-3"),
                Div(Field("date_scheduled"), css_class="col-lg-4"),
                css_class="row",
            ),
            Div(
                Div(Field("invoice"), css_class="col-lg-6"),
                Div(Field("proof_of_payment"), css_class="col-lg-6"),
                css_class="row",
            ),
            ButtonHolder(Submit("submit", "Submit", css_class="btn-sm")),
        )


class SubsidyAttachmentForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = (
            "subsidy",
            "attachment",
            "kind",
            "date",
            "description",
            "visibility",
        )

    def clean_attachment(self):
        attachment = self.cleaned_data["attachment"]
        filename_regex = (
            "^SciPost_"
            "[0-9]{4,}(-[0-9]{4,})?_[A-Z]{2,}_[\w]+_"
            "(Agreement|Invoice|ProofOfPayment|Other)"
            "(-[0-9]{2,})?(_[\w]+)?\.(pdf|docx|png)$"
        )
        pattern = re.compile(filename_regex)
        if not pattern.match(attachment.name):
            self.add_error(
                "attachment",
                "The filename does not match the required regex pattern "
                f"'{filename_regex}'",
            )
        return attachment


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
        empty_label="All",
    )
    start = forms.DateField(
        required=True, widget=forms.DateInput(attrs={"type": "date"})
    )
    end = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date"}))
    hourly_rate = forms.FloatField(min_value=0, initial=WorkLog.HOURLY_RATE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()

        if not any(self.fields[field].initial for field in ["start", "end"]):
            current_month = datetime.date.today().replace(day=1)
            last_month_end = current_month - datetime.timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            self.fields["start"].initial = last_month_start
            self.fields["end"].initial = last_month_end

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("employee"), css_class="col-9 col-md"),
                Div(FloatingField("hourly_rate"), css_class="col-3 col-md-2"),
                Div(FloatingField("start"), css_class="col-6 col-md-auto col-lg-2"),
                Div(FloatingField("end"), css_class="col-6 col-md-auto col-lg-2"),
                css_class="row mb-0 mt-2",
            ),
            Submit("submit", "Filter"),
        )

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

            work_log_qs = WorkLog.objects.filter(
                work_date__gte=self.cleaned_data["start"],
                work_date__lte=self.cleaned_data["end"],
                user__in=user_qs,
            )

            output = []
            for user in user_qs:
                # If logs exists for given filters
                total_time_per_month = [
                    work_log_qs.filter(
                        work_date__year=dt.year, work_date__month=dt.month, user=user
                    ).aggregate(Sum("duration"))["duration__sum"]
                    for dt in self.get_months()
                ]

                if self.cleaned_data["hourly_rate"]:
                    salary_per_month = [
                        duration.total_seconds()
                        / 3600  # Convert to hours
                        * self.cleaned_data["hourly_rate"]
                        if duration is not None
                        else 0
                        for duration in total_time_per_month
                    ]
                else:
                    salary_per_month = []

                output.append(
                    {
                        "monthly_data": zip(
                            self.get_months(),
                            total_time_per_month,
                            salary_per_month,
                        ),
                        "user": user,
                    }
                )

        return output
