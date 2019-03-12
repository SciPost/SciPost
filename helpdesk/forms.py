__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Queue


class QueueForm(forms.ModelForm):
    class Meta:
        model = Queue
        fields = ['name', 'slug', 'description',
                  'managing_group', 'response_groups',
                  'parent_queue']
