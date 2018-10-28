__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from ajax_select.fields import AutoCompleteSelectField

from .models import Topic


class SelectTagForm(forms.Form):
    tag = AutoCompleteSelectField('tag_lookup', label='Add Tag:', help_text='')
