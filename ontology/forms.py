__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from ajax_select.fields import AutoCompleteSelectField

from .constants import TOPIC_RELATIONS_ASYM


class SelectTagForm(forms.Form):
    tag = AutoCompleteSelectField('tag_lookup', label='', help_text='')


class SelectTopicForm(forms.Form):
    topic = AutoCompleteSelectField('topic_lookup')


class AddRelationAsymForm(forms.Form):
    A = AutoCompleteSelectField('topic_lookup', label='', help_text='')
    relation = forms.ChoiceField(choices=TOPIC_RELATIONS_ASYM, label='')
    B = AutoCompleteSelectField('topic_lookup', label='', help_text='')
