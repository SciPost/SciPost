__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime
import re

from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils.dates import MONTHS
from django.db.models import Q, Case, DateField, Max, Min, Sum, Value, When, F
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField

from dal import autocomplete
from dateutil.rrule import rrule, MONTHLY
from common.forms import HTMXDynSelWidget
from finances.constants import (
    SUBSIDY_STATUS,
    SUBSIDY_TYPE_SPONSORSHIPAGREEMENT,
    SUBSIDY_TYPES,
)

from organizations.models import Organization
from scipost.fields import UserModelChoiceField

from .models import Subsidy, SubsidyPayment, SubsidyAttachment, WorkLog


class SubsidyForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete",
            attrs={
                "data-html": True,
                "style": "width: 100%",
            },
        ),
    )

    renewal_of = forms.ModelMultipleChoiceField(
        queryset=Subsidy.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url=reverse_lazy("finances:subsidy_autocomplete"),
            attrs={
                "data-html": True,
                "style": "width: 100%",
            },
        ),
        help_text=("Start typing, and select from the popup."),
        required=False,
    )

    class Meta:
        model = Subsidy
        fields = [
            "algorithm",
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
    status = forms.MultipleChoiceField(
        label="Status",
        choices=SUBSIDY_STATUS,
        required=False,
    )
    type = forms.MultipleChoiceField(
        choices=SUBSIDY_TYPES,
        required=False,
    )
    active_year = forms.ChoiceField(
        label="Active year",
        required=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("amount", "Amount"),
            ("date_from", "Date from"),
            ("date_until", "Date until"),
            ("annot_renewal_action_date", "Renewal date"),
        ),
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Ascending"),
            ("+", "Descending"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("organization_query"), css_class="col"),
                        Div(
                            FloatingField("active_year"),
                            css_class="col-4 col-sm-3 col-md-2 col-lg-4 col-xl-3 col-xxl-2",
                        ),
                        css_class="row mb-0",
                    ),
                    Div(
                        Div(FloatingField("country"), css_class="col-12 col-lg-4"),
                        Div(FloatingField("orderby"), css_class="col-6 col-lg-4"),
                        Div(FloatingField("ordering"), css_class="col-6 col-lg-4"),
                        css_class="row mb-0",
                    ),
                    css_class="col-12 col-lg",
                ),
                Div(Field("status", size=6), css_class="col-12 col-lg-auto"),
                Div(Field("type", size=6), css_class="col-12 col-lg-auto"),
                css_class="row mb-0",
            ),
        )

        min_year, max_year = (
            Subsidy.objects.all()
            .aggregate(min=Min("date_from"), max=Max("date_until"))
            .values()
        )
        self.fields["active_year"].choices = [("", "---")] + [
            (year, year) for year in range(min_year.year, max_year.year + 1)
        ]

    def search_results(self, user):
        if user.groups.filter(name="Financial Administrators").exists():
            subsidies = Subsidy.objects.all()
        else:
            subsidies = Subsidy.objects.obtained()

        # Include `renewal_action_date` property in queryset
        subsidies = subsidies.annotate(
            annot_renewal_action_date=Case(
                When(
                    Q(subsidy_type=SUBSIDY_TYPE_SPONSORSHIPAGREEMENT),
                    then=F("date_until") - datetime.timedelta(days=122),
                ),
                default=Value(None),
                output_field=DateField(),
            )
        )

        if organization_query := self.cleaned_data["organization_query"]:
            subsidies = subsidies.filter(
                Q(organization__name__unaccent__icontains=organization_query)
                | Q(organization__acronym__unaccent__icontains=organization_query)
            )
        if self.cleaned_data["country"]:
            subsidies = subsidies.filter(
                organization__country__icontains=self.cleaned_data["country"],
            )

        if status := self.cleaned_data["status"]:
            subsidies = subsidies.filter(status__in=status)

        if subsidy_type := self.cleaned_data["type"]:
            subsidies = subsidies.filter(subsidy_type__in=subsidy_type)

        if active_year := self.cleaned_data["active_year"]:
            subsidies = subsidies.filter(
                Q(date_from__year__lte=int(active_year))
                & Q(date_until__year__gte=int(active_year))
            )

        # Ordering of subsidies
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            subsidies = subsidies.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

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
        widgets = {
            "date_scheduled": forms.DateInput(attrs={"type": "date"}),
        }

    invoice = forms.ChoiceField(required=False)
    proof_of_payment = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        subsidy = kwargs.pop("subsidy")
        super().__init__(*args, **kwargs)
        self.fields["subsidy"].initial = subsidy
        self.fields["subsidy"].widget = forms.HiddenInput()
        print(subsidy.attachments.invoices())
        self.fields["invoice"].choices = [
            (att.id, f"{att.attachment.name.split('/')[-1]}")
            for att in subsidy.attachments.invoices()
        ]
        self.fields["proof_of_payment"].choices = [
            (att.id, f"{att.attachment.name.split('/')[-1]}")
            for att in subsidy.attachments.proofs_of_payment()
        ]
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("subsidy"),
            Div(
                Div(Field("reference"), css_class="col-lg-5"),
                Div(Field("amount"), css_class="col-lg-3"),
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

    def clean_invoice(self):
        if invoice := self.cleaned_data["invoice"]:
            invoice = SubsidyAttachment.objects.get(id=invoice)
        return invoice

    def clean_proof_of_payment(self):
        if proof_of_payment := self.cleaned_data["proof_of_payment"]:
            proof_of_payment = SubsidyAttachment.objects.get(id=proof_of_payment)
        return proof_of_payment

    def save(self, commit=True):
        instance = super().save(commit=False)
        if invoice := self.cleaned_data["invoice"]:
            instance.invoice = invoice
        if proof_of_payment := self.cleaned_data["proof_of_payment"]:
            instance.proof_of_payment = proof_of_payment
        if commit:
            instance.save()
        return instance


class SubsidyAttachmentInlineLinkForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = []

    subsidy = forms.ModelChoiceField(
        queryset=Subsidy.objects.all(),
        widget=HTMXDynSelWidget(
            dynsel_context={
                "results_page_url": reverse_lazy(
                    "finances:_hx_dynsel_subsidy_result_page"
                ),
                "collection_name": "subsidies",
            }
        ),
        help_text=("Start typing, and select from the popup."),
        required=False,
    )

    subsidy_payment = forms.ModelChoiceField(
        queryset=SubsidyPayment.objects.none(),
        widget=forms.RadioSelect(),
        required=False,
    )

    payment_attachment_type = forms.ChoiceField(
        choices=(
            ("proof_of_payment", "Proof of payment"),
            ("invoice", "Invoice"),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["payment_attachment_type"].initial = "proof_of_payment"

        # Set the queryset to the payments of the subsidy if the subsidy is set
        if subsidy := self.initial.get("subsidy"):
            self.fields["subsidy_payment"].queryset = subsidy.payments.all()
        if subsidy_payment := self.initial.get("subsidy_payment"):
            self.fields["subsidy_payment"].initial = subsidy_payment

            if inferred_subsidy := getattr(subsidy_payment, "subsidy", None):
                self.fields["subsidy"].initial = inferred_subsidy
                self.fields["subsidy_payment"].queryset = (
                    inferred_subsidy.payments.all()
                )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("subsidy"), css_class="col-5 col"),
                Div(Field("payment_attachment_type"), css_class="col-2 col"),
                Div(Field("subsidy_payment"), css_class="col-5 col"),
                css_class="row mb-0",
            )
        )

    def clean_subsidy(self):
        return

    def clean(self):
        return self.cleaned_data

    def save(self):
        # Link to payment
        if subsidy_payment := self.cleaned_data["subsidy_payment"]:
            if attachment_type := self.cleaned_data["payment_attachment_type"]:
                setattr(subsidy_payment, attachment_type, self.instance)

            self.instance.subsidy = subsidy_payment.subsidy

        subsidy_payment.save()
        self.instance.save()

        return self.instance

    def clean_subsidy_payment(self):
        if subsidy_payment := self.cleaned_data["subsidy_payment"]:
            subsidy_payment = SubsidyPayment.objects.get(id=subsidy_payment.id)
        else:
            self.add_error("subsidy_payment", "Please select a payment")
        return subsidy_payment


class SubsidyAttachmentForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = (
            "subsidy",
            "attachment",
            "git_url",
            "kind",
            "date",
            "description",
            "visibility",
        )
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    subsidy = forms.ModelChoiceField(
        queryset=Subsidy.objects.all(),
        widget=autocomplete.ModelSelect2(
            url=reverse_lazy("finances:subsidy_autocomplete"),
            attrs={
                "data-html": True,
                "style": "width: 100%",
            },
        ),
        help_text=("Start typing, and select from the popup."),
        required=False,
    )

    # def clean(self):
    #     orphaned = self.cleaned_data["subsidy"] is None
    #     attachment_filename = self.cleaned_data["attachment"].name.split("/")[-1]

    #     # Allow misnamed orphans
    #     if orphaned:
    #         return

    #     filename_regex = (
    #         "^SciPost_"
    #         "[0-9]{4,}(-[0-9]{4,})?_[A-Z]{2,}_[\w]+_"
    #         "(Agreement|Invoice|ProofOfPayment|Other)"
    #         "(-[0-9]{2,})?(_[\w]+)?\.(pdf|docx|png)$"
    #     )
    #     pattern = re.compile(filename_regex)

    #     #
    #     if not pattern.match(attachment_filename):
    #         self.add_error(
    #             "attachment",
    #             "The filename does not match the required regex pattern "
    #             f"'{filename_regex}'",
    #         )


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
                        (
                            duration.total_seconds()
                            / 3600  # Convert to hours
                            * self.cleaned_data["hourly_rate"]
                            if duration is not None
                            else 0
                        )
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
