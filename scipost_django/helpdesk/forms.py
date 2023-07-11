__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import Queue, Ticket, Followup
from .constants import TICKET_PRIORITIES, TICKET_STATUSES
from crispy_forms.helper import FormHelper, Layout
from crispy_bootstrap5.bootstrap5 import FloatingField, Field
from crispy_forms.layout import Div
from django.db.models import Q


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
        group_ids = [
            k["id"]
            for k in list(self.instance.queue.response_groups.all().values("id"))
        ]
        group_ids.append(self.instance.queue.managing_group.id)
        self.fields["assigned_to"].queryset = User.objects.filter(
            groups__id__in=group_ids
        ).distinct()


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
    priority = forms.MultipleChoiceField(choices=TICKET_PRIORITIES, required=False)
    status = forms.MultipleChoiceField(choices=TICKET_STATUSES, required=False)

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("defined_on", "Opened date"),
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

    def __init__(self, *args, **kwargs):
        if queue_slug := kwargs.pop("queue_slug", None):
            self.queue = get_object_or_404(Queue, slug=queue_slug)
            self.tickets = Ticket.objects.filter(queue=self.queue)
        else:
            self.tickets = Ticket.objects.all()
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(Field("priority", size=4), css_class="col-12"),
                        Div(FloatingField("title"), css_class="col-12"),
                        css_class="row mb-0",
                    ),
                    css_class="col-6",
                ),
                Div(Field("status", size=8), css_class="col-6"),
                Div(FloatingField("description"), css_class="col-12"),
                css_class="row mb-0",
            ),
            Div(
                Div(Field("ordering"), css_class="col-6"),
                Div(Field("orderby"), css_class="col-6"),
                css_class="row mb-0",
            ),
        )

    def search_results(self):
        tickets = self.tickets

        if title := self.cleaned_data.get("title"):
            tickets = tickets.filter(title__icontains=title)
        if description := self.cleaned_data.get("description"):
            tickets = tickets.filter(description__icontains=description)

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
