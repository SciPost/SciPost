__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Queue, Ticket, Followup


class QueueForm(forms.ModelForm):
    class Meta:
        model = Queue
        fields = ['name', 'slug', 'description',
                  'managing_group', 'response_groups',
                  'parent_queue']


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['queue', 'title', 'description', 'publicly_visible',
                  'defined_on', 'defined_by', 'priority',
                  'deadline', 'status',
                  'concerning_object_type', 'concerning_object_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['defined_on'].widget = forms.HiddenInput()
        self.fields['defined_on'].disabled = True
        # self.fields['defined_by'].widget = forms.HiddenInput()
        # self.fields['defined_by'].disabled = True
        self.fields['deadline'].widget = forms.HiddenInput()
        self.fields['deadline'].disabled = True
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['status'].disabled = True
        self.fields['concerning_object_type'].widget = forms.HiddenInput()
        self.fields['concerning_object_type'].disabled=True
        self.fields['concerning_object_id'].widget = forms.HiddenInput()
        self.fields['concerning_object_id'].disabled = True


class FollowupForm(forms.ModelForm):
    class Meta:
        model = Followup
        fields = ['ticket', 'text', 'by', 'timestamp', 'action']
