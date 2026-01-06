__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.functions import Concat
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms

from common.forms import CrispyFormMixin, FormOptionsStorageMixin, SearchForm
from profiles.models import Profile

from .models import Queue, Ticket, Followup
from .constants import TICKET_PRIORITIES, TICKET_STATUS_ASSIGNED, TICKET_STATUSES
from crispy_forms.helper import Layout
from crispy_bootstrap5.bootstrap5 import Field
from crispy_forms.layout import Div
from django.db.models import (
    Q,
    Case,
    CharField,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
    When,
)


class QueueForm(forms.ModelForm):
    class Meta:
        model = Queue
        fields = [
            "name",
            "slug",
            "description",
            "managing_group",
            "response_groups",
            "parent_queue",
        ]


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "queue",
            "title",
            "description",
            "defined_on",
            "defined_by",
            "priority",
            "publicly_visible",
            "deadline",
            "status",
            "concerning_object_type",
            "concerning_object_id",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update(
            {
                "placeholder": '[meaningful, short label, e.g. "Broken link on Publication page"]'
            }
        )
        self.fields["defined_on"].widget = forms.HiddenInput()
        self.fields["defined_on"].disabled = True
        self.fields["defined_by"].widget = forms.HiddenInput()
        self.fields["deadline"].widget = forms.HiddenInput()
        self.fields["deadline"].disabled = True
        self.fields["status"].widget = forms.HiddenInput()
        self.fields["status"].disabled = True
        self.fields["concerning_object_type"].widget = forms.HiddenInput()
        self.fields["concerning_object_id"].widget = forms.HiddenInput()
        self.fields["concerning_object_id"].disabled = True


class TicketAssignForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "assigned_to",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assigned_to"].queryset = User.objects.filter(
            groups__id__in=list(
                self.instance.queue.response_groups.all().values_list("id", flat=True)
            )
            + [self.instance.queue.managing_group.id]
        ).distinct()

    def save(self, commit=True):
        ticket = super().save(commit=False)
        ticket.status = TICKET_STATUS_ASSIGNED

        # Remove old view permissions
        can_view_users = get_users_with_perms(
            ticket, only_with_perms_in=["can_view_ticket"]
        )
        for user in can_view_users:
            remove_perm("can_view_ticket", user, ticket)

        # Assign view permission to assignee
        assign_perm("can_view_ticket", ticket.assigned_to, ticket)

        if commit:
            ticket.save()
        return ticket


class FollowupForm(forms.ModelForm):
    class Meta:
        model = Followup
        fields = ["ticket", "text", "by", "timestamp", "action"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ticket"].widget = forms.HiddenInput()
        self.fields["by"].widget = forms.HiddenInput()
        self.fields["timestamp"].widget = forms.HiddenInput()
        self.fields["action"].widget = forms.HiddenInput()


class TicketSearchForm(CrispyFormMixin, FormOptionsStorageMixin, SearchForm[Ticket]):
    title = forms.CharField(max_length=64, required=False)
    description = forms.CharField(max_length=512, required=False)
    assigned_to = forms.MultipleChoiceField(
        required=False, choices=[("0", "Unassigned")]
    )
    defined_by = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Name, email, or ORCID. Partial matches may not work as expected."
            }
        ),
    )
    priority = forms.MultipleChoiceField(
        choices=[(key, key.title()) for key, _ in TICKET_PRIORITIES], required=False
    )
    status = forms.MultipleChoiceField(choices=TICKET_STATUSES, required=False)
    concerning_object = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "ID of concerning object"}),
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("defined_on", "Defined on"),
            ("defined_by__contributor__profile__last_name", "Last name"),
            ("defined_by__contributor__profile__first_name", "First name"),
            ("followups__latest__timestamp", "Latest activity"),
            ("status", "Status"),
            ("priority", "Priority"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        if not (user := kwargs.pop("user", None)):
            raise ValueError("user is required to filter the tickets")

        if queue := kwargs.pop("queue", None):
            self.queue = queue
            self.queryset = Ticket.objects.filter(queue=self.queue)
        else:
            self.queryset = Ticket.objects.all()

        super().__init__(*args, **kwargs)

        self.queryset = self.queryset.visible_by(user)

        self.fields["assigned_to"].choices += (
            User.objects.filter(
                pk__in=self.queryset.values_list("assigned_to", flat=True).distinct()
            )
            .annotate(
                full_name=Concat(
                    "contributor__profile__first_name",
                    Value(" "),
                    "contributor__profile__last_name",
                    output_field=CharField(),
                )
            )
            .values_list("id", "full_name")
        )

    def get_form_layout(self) -> Layout:
        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-12"),
            Div(Field("ordering"), css_class="col-12"),
            css_class="row mb-0",
        )

        return Layout(
            Div(
                Div(Field("title"), css_class="col-12 col-md-6"),
                Div(Field("defined_by"), css_class="col-12 col-md-6"),
                Div(Field("description"), css_class="col-12 col-md"),
                Div(Field("concerning_object"), css_class="col-12 col-md-4"),
                css_class="row",
            ),
            Div(
                Div(Field("assigned_to", size=7), css_class="col-12 col-sm-6 col-lg"),
                Div(Field("status", size=7), css_class="col-12 col-sm-6 col-lg"),
                Div(
                    Field("priority", size=5), css_class="col-auto col-sm-6 col-lg-auto"
                ),
                Div(div_block_ordering, css_class="col col-sm-6 col-md"),
                css_class="row",
            ),
        )

    def filter_queryset(self, queryset: QuerySet[Ticket]) -> QuerySet[Ticket]:
        if title := self.cleaned_data.get("title"):
            queryset = queryset.filter(title__icontains=title)
        if description := self.cleaned_data.get("description"):
            queryset = queryset.filter(description__icontains=description)
        if defined_by := self.cleaned_data.get("defined_by"):
            profiles_matched = Profile.objects.search(defined_by)
            queryset = queryset.filter(
                defined_by__contributor__profile__in=profiles_matched
            )
        if concerning_object := self.cleaned_data.get("concerning_object"):
            from submissions.models import Submission, Report

            # If the concerning object is a submission, also check it preprint identifier
            report_type = ContentType.objects.get_for_model(Report)
            submission_type = ContentType.objects.get_for_model(Submission)
            queryset = queryset.annotate(
                preprint_id=Case(
                    When(
                        concerning_object_type=submission_type,
                        then=Subquery(
                            Submission.objects.filter(
                                pk=OuterRef("concerning_object_id")
                            ).values("preprint__identifier_w_vn_nr")
                        ),
                    ),
                    When(
                        concerning_object_type=report_type,
                        then=Subquery(
                            Report.objects.filter(
                                pk=OuterRef("concerning_object_id")
                            ).values("submission__preprint__identifier_w_vn_nr")
                        ),
                    ),
                    default=Value(""),
                    output_field=CharField(),
                )
            )

            # Include matches with the concerning object preprint ID
            Q_concerning_object = Q(preprint_id__icontains=concerning_object)

            # Include matches with the concerning object ID if input is an integer
            if concerning_object.isdigit():
                Q_concerning_object |= Q(concerning_object_id=concerning_object)

            queryset = queryset.filter(
                Q(concerning_object_id__isnull=False) & Q_concerning_object
            )

        queryset = self.data_is_in_or_null(queryset, "priority", "priority")
        queryset = self.data_is_in_or_null(queryset, "status", "status")
        queryset = self.data_is_in_or_null(queryset, "assigned_to", "assigned_to")

        return queryset
