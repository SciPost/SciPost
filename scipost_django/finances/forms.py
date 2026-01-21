__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import timedelta, date
from itertools import groupby

from django import forms
from django.contrib.auth import get_user_model
from django.db.models.functions import (
    Coalesce,
    ExtractHour,
    ExtractMinute,
    ExtractSecond,
)
from django.urls import reverse_lazy
from django.db.models import (
    Q,
    Case,
    DateField,
    Max,
    Min,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
    When,
    F,
)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField

from dal import autocomplete
from careers.models import WorkContract
from common.forms import CrispyFormMixin, HTMXDynSelWidget, SearchForm
from common.utils.models import RelatedAttachment, attach_related
from finances.constants import (
    SUBSIDY_STATUS,
    SUBSIDY_TYPE_SPONSORSHIPAGREEMENT,
    SUBSIDY_TYPES,
    SUBSIDY_TYPE_INDIVIDUAL_BUDGET,
)

from finances.models.subsidy import SubsidyCollective
from finances.utils.compensations import CompensationStrategy
from funders.models import IndividualBudget
from organizations.models import Organization
from production.constants import WORK_LOG_TYPE_TIME_OFF
from production.models import ProductionStream
from scipost.fields import UserModelChoiceField

from .models import Subsidy, SubsidyPayment, SubsidyAttachment, WorkLog
from .models.work_log import HOURLY_RATE


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

    compensation_strategies_keys = forms.MultipleChoiceField(
        choices=CompensationStrategy.get_choices(),
        widget=forms.SelectMultiple(attrs={"size": 5}),
        label="Compensation Strategies",
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
            "collective",
            "individual_budget",
            "compensation_strategies_keys",
            "compensation_strategies_details",
        ]
        widgets = {
            "paid_on": forms.DateInput(attrs={"type": "date"}),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CREATE_URL = 'If missing, <a href="{url}">create a new one</a>.'
        self.fields["collective"].help_text = CREATE_URL.format(
            url=reverse_lazy("finances:subsidy_collective_create")
        )
        self.fields["individual_budget"].help_text = CREATE_URL.format(
            url=reverse_lazy("funders:individual_budget_create")
        )

    def clean(self):
        cleaned_data = super().clean()

        individual_budget: "IndividualBudget | None" = cleaned_data.get(
            "individual_budget", None
        )

        # Validate individual budget subsidies
        if cleaned_data.get("subsidy_type") == SUBSIDY_TYPE_INDIVIDUAL_BUDGET:
            if cleaned_data.get("renewable"):
                self.add_error(
                    "renewable",
                    "Individual budget subsidies are not renewable",
                )

            if not individual_budget:
                self.add_error(
                    "individual_budget",
                    "An individual budget must be selected",
                )
            elif individual_budget.organization and (
                individual_budget.organization != cleaned_data.get("organization")
            ):
                self.add_error(
                    "organization",
                    "The selected Organization does not match the one providing the individual budget",
                )

            if cleaned_data.get("date_from") != cleaned_data.get("date_until"):
                self.add_error(
                    "date_until",
                    "Individual budget subsidies must have the same from and until date",
                )

        return cleaned_data


class SubsidySearchForm(CrispyFormMixin, SearchForm[Subsidy]):
    model = Subsidy

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
        initial="date_from",
        required=False,
    )

    def get_form_layout(self) -> Layout:
        return Layout(
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        min_year, max_year = (
            Subsidy.objects.all()
            .aggregate(min=Min("date_from"), max=Max("date_until"))
            .values()
        )
        self.fields["active_year"].choices = [("", "Any")] + [
            (year, year) for year in range(min_year.year, max_year.year + 1)
        ]

    def filter_queryset(self, queryset: "QuerySet[Subsidy]") -> "QuerySet[Subsidy]":
        if not self.user.groups.filter(name="Financial Administrators").exists():
            queryset = queryset.obtained()

        # Include `renewal_action_date` property in queryset
        queryset = queryset.annotate(
            annot_renewal_action_date=Case(
                When(
                    Q(subsidy_type=SUBSIDY_TYPE_SPONSORSHIPAGREEMENT),
                    then=F("date_until") - datetime.timedelta(days=122),
                ),
                default=Value(None),
                output_field=DateField(),
            )
        )

        if organization_query := self.cleaned_data.get("organization_query"):
            queryset = queryset.filter(
                Q(organization__name__unaccent__icontains=organization_query)
                | Q(organization__name_original__unaccent__icontains=organization_query)
                | Q(organization__acronym__unaccent__icontains=organization_query)
            )
        if country := self.cleaned_data.get("country"):
            queryset = queryset.filter(organization__country__icontains=country)

        if status := self.cleaned_data.get("status"):
            queryset = queryset.filter(status__in=status)

        if subsidy_type := self.cleaned_data.get("type"):
            queryset = queryset.filter(subsidy_type__in=subsidy_type)

        if active_year := self.cleaned_data.get("active_year"):
            queryset = queryset.filter(
                Q(date_from__year__lte=int(active_year))
                & Q(date_until__year__gte=int(active_year))
            )

        return queryset.distinct()


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

        invoice_qs = subsidy.attachments.unattached().invoices()
        if self.instance.invoice:
            invoice_qs |= SubsidyAttachment.objects.filter(id=self.instance.invoice.id)
            self.fields["invoice"].initial = self.instance.invoice.id

        proofs_qs = subsidy.attachments.unattached().proofs_of_payment()
        if self.instance.proof_of_payment:
            proofs_qs |= SubsidyAttachment.objects.filter(
                id=self.instance.proof_of_payment.id
            )
            self.fields["proof_of_payment"].initial = self.instance.proof_of_payment.id

        self.fields["invoice"].choices = [(None, "---")] + [
            (att.id, f"{att.attachment.name.split('/')[-1]}") for att in invoice_qs
        ]
        self.fields["proof_of_payment"].choices = [(None, "---")] + [
            (att.id, f"{att.attachment.name.split('/')[-1]}") for att in proofs_qs
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
        instance.invoice = self.cleaned_data["invoice"] or None
        instance.proof_of_payment = self.cleaned_data["proof_of_payment"] or None
        if commit:
            instance.save()
        return instance


class SubsidyPaymentAmountDateChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: SubsidyPayment):
        return f"{obj.status} €{obj.amount} on {obj.date_scheduled}"


class SubsidyAttachmentInlineLinkForm(forms.ModelForm):
    class Meta:
        model = SubsidyAttachment
        fields = []

    subsidy = forms.ModelChoiceField(
        queryset=Subsidy.objects.all(),
        widget=HTMXDynSelWidget(
            url=reverse_lazy("finances:subsidy_dynsel"),
        ),
        help_text=("Start typing, and select from the popup."),
        required=False,
    )

    subsidy_payment = SubsidyPaymentAmountDateChoiceField(
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

        if subsidy_payment := self.initial.get("subsidy_payment"):
            self.fields["subsidy_payment"].initial = subsidy_payment

            # Set the queryset to the payments of the subsidy if the subsidy is set
            # or infer subsidy from subsidy payment
            initial_subsidy = self.initial.get("subsidy")
            if subsidy := getattr(subsidy_payment, "subsidy", initial_subsidy):
                self.fields["subsidy"].initial = subsidy
                self.fields["subsidy_payment"].queryset = subsidy.payments.all()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("subsidy"), css_class="col-5 col"),
                Div(Field("payment_attachment_type"), css_class="col-2 col"),
                Div(Field("subsidy_payment"), css_class="col-5 col"),
                css_class="row mb-0",
            )
        )

    # def clean_subsidy(self):
    #     return

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


from django.contrib.postgres.forms.ranges import DateRangeField


class SubsidyAttachmentSearchForm(CrispyFormMixin, SearchForm[SubsidyAttachment]):
    model = SubsidyAttachment
    queryset = SubsidyAttachment.objects.orphaned()
    form_id = "subsidyattachment-orphaned-search-form"

    kind = forms.MultipleChoiceField(
        choices=SubsidyAttachment.KIND_CHOICES,
        required=False,
    )

    filename = forms.CharField(
        max_length=128,
        required=False,
        label="Filename",
    )

    description = forms.CharField(
        max_length=128,
        required=False,
    )

    visibility = forms.ChoiceField(
        choices=[("", "Any")] + list(SubsidyAttachment.VISIBILITY_CHOICES),
        required=False,
    )

    # is_orphaned = forms.BooleanField(
    #     required=False,
    #     label="Orphaned",
    # )

    date_from = forms.DateField(
        label="From date",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    date_to = forms.DateField(
        label="To date",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("date", "Date"),
            ("attachment", "Filename"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def get_form_layout(self) -> Layout:
        div_block_ordering = Div(
            Div(FloatingField("orderby"), css_class="col-6 col-md-12 col-xl-6"),
            Div(FloatingField("ordering"), css_class="col-6 col-md-12 col-xl-6"),
            css_class="row mb-0",
        )
        div_block_checkbox = Div(
            Div(Field("is_orphaned"), css_class="col-auto col-lg-12 col-xl-auto"),
            css_class="row mb-0",
        )
        div_block_dates = Div(
            Div(Field("date_from"), css_class="col-6"),
            Div(Field("date_to"), css_class="col-6"),
            css_class="row mb-0",
        )

        return Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("filename"), css_class="col"),
                        Div(
                            FloatingField("visibility"),
                            css_class="col-3 col-md-4 col-lg-2",
                        ),
                        Div(FloatingField("description"), css_class="col-12"),
                        Div(div_block_ordering, css_class="col-12 col-md-6 col-xl-12"),
                        Div(div_block_checkbox, css_class="col-12 col-md-6 col-xl-12"),
                        css_class="row mb-0",
                    ),
                    css_class="col",
                ),
                Div(
                    Field("kind", size=4),
                    Div(div_block_dates, css_class="col-12"),
                    css_class="col-12 col-md-6 col-lg-4",
                ),
                css_class="row mb-0",
            ),
        )

    def filter_queryset(
        self, queryset: "QuerySet[SubsidyAttachment]"
    ) -> "QuerySet[SubsidyAttachment]":
        if filename := self.cleaned_data.get("filename"):
            queryset = queryset.filter(attachment__icontains=filename)
        if description := self.cleaned_data.get("description"):
            queryset = queryset.filter(description__icontains=description)
        if visibility := self.cleaned_data.get("visibility"):
            queryset = queryset.filter(visibility=visibility)
        if kind := self.cleaned_data.get("kind"):
            queryset = queryset.filter(kind__in=kind)
        if (date_from := self.cleaned_data.get("date_from")) and (
            date_to := self.cleaned_data.get("date_to")
        ):
            queryset = queryset.filter(date__gte=date_from, date__lte=date_to)

        # if is_orphaned := self.cleaned_data.get("is_orphaned"):
        #     subsidy_attachments = subsidy_attachments.orphaned()

        return queryset


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
        required=True,
        label="Start date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end = forms.DateField(
        required=True,
        label="End date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not any(self.fields[field].initial for field in ["start", "end"]):
            current_month = date.today().replace(day=1)
            last_month_end = current_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            self.fields["start"].initial = last_month_start
            self.fields["end"].initial = last_month_end

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("employee"), css_class="col-12 col-md"),
                Div(FloatingField("start"), css_class="col-6 col-md-auto col-lg-2"),
                Div(FloatingField("end"), css_class="col-6 col-md-auto col-lg-2"),
                css_class="row mb-0 mt-2",
            ),
            Submit("submit", "Filter"),
        )

    def get_timesheets(self):
        WEEKS_IN_MONTH = 4 + 1 / 3  # approx.
        DEFAULT_HOURLY_RATE = 24.0
        DEFAULT_WORK_HOURS = 0

        contract_subq = WorkContract.objects.filter(
            Q(end_date__gte=OuterRef("work_date")) | Q(end_date__isnull=True),
            start_date__lte=OuterRef("work_date"),
            employee=OuterRef("user__contributor"),
            salary_type=WorkContract.SALARY_TYPE_HOURLY,
        ).order_by("-start_date")

        work_logs = (
            WorkLog.objects.filter(
                work_date__gte=self.cleaned_data["start"],
                work_date__lte=self.cleaned_data["end"],
            )
            .annotate(
                full_name=F("user__contributor__profile__full_name"),
                active_contract=Subquery(contract_subq.values("id")[:1]),
                duration_in_seconds=Coalesce(
                    ExtractHour("duration") * 3600
                    + ExtractMinute("duration") * 60
                    + ExtractSecond("duration"),
                    Value(0),
                ),
            )
            .order_by("full_name", "-work_date")
        )

        if employee := self.cleaned_data.get("employee"):
            work_logs = work_logs.filter(user=employee)

        # Attach related WorkContract objects to avoid N+1 queries
        attach_related(
            work_logs,
            RelatedAttachment(
                "active_contract", "contract", WorkContract.objects.all()
            ),
            RelatedAttachment(
                "object_id",
                "stream",
                queryset=ProductionStream.objects.select_related(
                    "submission",
                    "proofs_repository",
                ),
            ),
        )

        for wl in work_logs:
            if not wl.contract:
                wl.hourly_rate = DEFAULT_HOURLY_RATE
                wl.work_hours_week = DEFAULT_WORK_HOURS
                continue

            wl.hourly_rate = wl.contract.pay_rate
            wl.work_hours_week = wl.contract.work_hours_week.total_seconds() / 3600

        timesheets = []
        for (full_name, year, month), working_logs in groupby(
            work_logs,
            key=lambda wl: (wl.full_name, wl.work_date.year, wl.work_date.month),
        ):
            all_user_work_logs = list(working_logs)
            if not all_user_work_logs:
                continue

            base_hours_week = float(all_user_work_logs[0].work_hours_week)
            hourly_rate = float(all_user_work_logs[0].hourly_rate)

            real_work_hours = sum(
                wl.duration_in_seconds / 3600
                for wl in all_user_work_logs
                if wl.log_type != WORK_LOG_TYPE_TIME_OFF
            )
            daysoff_hours = sum(
                wl.duration_in_seconds / 3600
                for wl in all_user_work_logs
                if wl.log_type == WORK_LOG_TYPE_TIME_OFF
            )
            base_hours_month = base_hours_week * WEEKS_IN_MONTH
            work_hours = real_work_hours + daysoff_hours
            extra_hours_month = max(0, work_hours - base_hours_month)
            total_duration = base_hours_month + extra_hours_month

            timesheets.append(
                {
                    "full_name": full_name,
                    "date": date(year, month, 1),
                    "base_hours": timedelta(hours=base_hours_month),
                    "extra_hours": timedelta(hours=extra_hours_month),
                    "paid_time_off": timedelta(hours=daysoff_hours),
                    "total_hours": timedelta(hours=total_duration),
                    "pay_rate": hourly_rate,
                    "total_compensation": round(hourly_rate * total_duration, 2),
                    "work_logs": all_user_work_logs,
                }
            )

        timesheets.sort(key=lambda ts: (ts["date"], ts["full_name"]))

        return timesheets


class SubsidyCollectiveForm(forms.ModelForm):
    required_css_class = "required-asterisk"

    subsidies = forms.ModelMultipleChoiceField(
        queryset=Subsidy.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url=reverse_lazy("finances:subsidy_autocomplete"),
            attrs={
                "data-html": True,
                "style": "width: 100%",
            },
        ),
        required=False,
    )

    class Meta:
        model = SubsidyCollective
        fields = ["name", "description", "coordinator"]
        widgets = {
            "coordinator": autocomplete.ModelSelect2(
                url=reverse_lazy("organizations:organization-autocomplete"),
                attrs={
                    "data-html": True,
                    "style": "width: 100%",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["subsidies"].initial = self.instance.subsidies.all()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("name"),
            Field("description"),
            Field("coordinator"),
            Field("subsidies"),
            ButtonHolder(Submit("submit", "Submit", css_class="btn-sm")),
        )

    def save(self, commit: bool = True):
        collective = super().save(commit)

        collective.subsidies.set(self.cleaned_data["subsidies"])
        return collective


class SubsidyCollectiveRenewForm(forms.Form):
    subsidies = forms.ModelMultipleChoiceField(
        queryset=Subsidy.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.collective = kwargs.pop("collective")
        super().__init__(*args, **kwargs)
        self.fields["subsidies"].queryset = self.collective.subsidies.all()
        self.fields["subsidies"].initial = self.fields["subsidies"].queryset

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field("subsidies", css_class="col-12"),
                Div(FloatingField("start_date"), css_class="col-6"),
                Div(FloatingField("end_date"), css_class="col-6"),
                css_class="row mb-0",
            ),
            ButtonHolder(Submit("submit", "Renew", css_class="btn-sm")),
        )

    def clean(self):
        valid = self.is_valid()
        if not (data := self.cleaned_data):
            raise forms.ValidationError("No data was submitted")
        elif not valid:
            raise forms.ValidationError("Invalid form data")

        start = data.get("start_date")
        end = data.get("end_date")

        if start > end:
            self.add_error("end_date", "End date must be after start date")

        return data

    def save(self):
        start_date = self.cleaned_data["start_date"]
        end_date = self.cleaned_data["end_date"]

        new_subsidies = [
            Subsidy(
                organization=subsidy.organization,
                subsidy_type=subsidy.subsidy_type,
                description=subsidy.description,
                amount=subsidy.amount,
                amount_publicly_shown=subsidy.amount_publicly_shown,
                status=subsidy.status,
                paid_on=subsidy.paid_on,
                renewable=subsidy.renewable,
                # Renewal dates are optional
                date_from=start_date or subsidy.date_from,
                date_until=end_date or subsidy.date_until,
            )
            for subsidy in self.cleaned_data["subsidies"]
        ]

        # Create new subsidies
        Subsidy.objects.bulk_create(new_subsidies)

        # Update `renewal_of` field to point to the original subsidy
        for new, old in zip(new_subsidies, self.cleaned_data["subsidies"]):
            new.renewal_of.add(old)
            new.save()

        # Create new collective
        new_collective = SubsidyCollective.objects.create(
            name=f"{self.collective.name} - Renewal {start_date} - {end_date}",
            description=f"{self.collective.description}\n Renewal {start_date} - {end_date}",
            coordinator=self.collective.coordinator,
        )
        new_collective.subsidies.set(new_subsidies)
        new_collective.save()

        return new_collective
