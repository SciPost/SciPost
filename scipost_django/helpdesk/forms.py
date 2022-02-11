__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User

from .models import Queue, Ticket, Followup


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
