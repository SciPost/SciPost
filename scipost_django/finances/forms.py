__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils.dates import MONTHS
from django.db.models import Sum
from django.utils import timezone

from dal import autocomplete
from dateutil.rrule import rrule, MONTHLY

from organizations.models import Organization
from scipost.fields import UserModelChoiceField

from .models import Subsidy, SubsidyAttachment, WorkLog


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
            "date",
            "date_until",
            "renewable",
            "renewal_of",
        ]


class SubsidyAttachmentForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = (
            "subsidy",
            "attachment",
            "kind",
            "name",
            "description",
            "name",
            "visibility",
        )


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
