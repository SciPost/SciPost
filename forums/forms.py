__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Forum


class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'slug', 'publicly_visible', 'moderators']
