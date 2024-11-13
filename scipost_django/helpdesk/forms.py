__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.db import SessionStore
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms

from profiles.models import Profile

from .models import Queue, Ticket, Followup
from .constants import TICKET_PRIORITIES, TICKET_STATUS_ASSIGNED, TICKET_STATUSES
from crispy_forms.helper import FormHelper, Layout
from crispy_bootstrap5.bootstrap5 import FloatingField, Field
from crispy_forms.layout import Div
from django.db.models import Q, Case, CharField, OuterRef, Subquery, Value, When


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


class TicketSearchForm(forms.Form):
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
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Descending"),
            ("+", "Ascending"),
        ),
        required=False,
    )

    def save_fields_to_session(self):
        # Save the form data to the session
        if self.session_key is not None:
            session = SessionStore(session_key=self.session_key)

            for field_key in self.cleaned_data:
                session_key = (
                    f"{self.form_id}_{field_key}"
                    if hasattr(self, "form_id")
                    else field_key
                )

                if field_value := self.cleaned_data.get(field_key):
                    if isinstance(field_value, datetime.date):
                        field_value = field_value.strftime("%Y-%m-%d")

                session[session_key] = field_value

            session.save()

    def apply_filter_set(self, filters: dict, none_on_empty: bool = False):
        # Apply the filter set to the form
        for key in self.fields:
            if key in filters:
                self.fields[key].initial = filters[key]
            elif none_on_empty:
                if isinstance(self.fields[key], forms.MultipleChoiceField):
                    self.fields[key].initial = []
                else:
                    self.fields[key].initial = None

    def __init__(self, *args, **kwargs):
        if not (user := kwargs.pop("user", None)):
            raise ValueError("user is required to filter the tickets")

        self.session_key = kwargs.pop("session_key", None)
        if queue := kwargs.pop("queue", None):
            self.queue = queue
            self.tickets = Ticket.objects.filter(queue=self.queue)
        else:
            self.tickets = Ticket.objects.all()

        self.tickets = self.tickets.visible_by(user)

        super().__init__(*args, **kwargs)

        self.fields["assigned_to"].choices += (
            User.objects.filter(
                pk__in=self.tickets.values_list("assigned_to", flat=True).distinct()
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

        # Set the initial values of the form fields from the session data
        # if self.session_key:
        #     session = SessionStore(session_key=self.session_key)

        #     for field_key in self.fields:
        #         session_key = (
        #             f"{self.form_id}_{field_key}"
        #             if hasattr(self, "form_id")
        #             else field_key
        #         )

        #         if session_value := session.get(session_key):
        #             self.fields[field_key].initial = session_value

        self.helper = FormHelper()

        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-12"),
            Div(Field("ordering"), css_class="col-12"),
            css_class="row mb-0",
        )

        self.helper.layout = Layout(
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

    def search_results(self):
        # self.save_fields_to_session()

        tickets = self.tickets

        if title := self.cleaned_data.get("title"):
            tickets = tickets.filter(title__icontains=title)
        if description := self.cleaned_data.get("description"):
            tickets = tickets.filter(description__icontains=description)
        if defined_by := self.cleaned_data.get("defined_by"):
            profiles_matched = Profile.objects.search(defined_by)
            tickets = tickets.filter(
                defined_by__contributor__profile__in=profiles_matched
            )
        if concerning_object := self.cleaned_data.get("concerning_object"):
            from submissions.models import Submission, Report

            # If the concerning object is a submission, also check it preprint identifier
            report_type = ContentType.objects.get_for_model(Report)
            submission_type = ContentType.objects.get_for_model(Submission)
            tickets = tickets.annotate(
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

            tickets = tickets.filter(
                Q(concerning_object_id__isnull=False) & Q_concerning_object
            )

        def is_in_or_null(queryset, key, value, implicit_all=True):
            """
            Filter a queryset by a list of values. If the list contains a 0, then
            also include objects where the key is null. If the list is empty, then
            include all objects if implicit_all is True.
            """
            value = self.cleaned_data.get(value)
            has_unassigned = "0" in value
            is_unassigned = Q(**{key + "__isnull": True})
            is_in_values = Q(**{key + "__in": list(filter(lambda x: x != 0, value))})

            if has_unassigned:
                return queryset.filter(is_unassigned | is_in_values)
            elif implicit_all and not value:
                return queryset
            else:
                return queryset.filter(is_in_values)

        tickets = is_in_or_null(tickets, "priority", "priority")
        tickets = is_in_or_null(tickets, "status", "status")
        tickets = is_in_or_null(tickets, "assigned_to", "assigned_to")

        # Ordering of streams
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            tickets = tickets.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        return tickets
