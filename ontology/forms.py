__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from ajax_select.fields import AutoCompleteSelectField

from .constants import TOPIC_RELATIONS_ASYM


class SelectTagForm(forms.Form):
    tag = AutoCompleteSelectField('tag_lookup', label='', help_text='')


class SelectTopicForm(forms.Form):
    topic = AutoCompleteSelectField('topic_lookup', label='', help_text='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic'].widget.attrs.update({
            'placeholder':'type here to find topic'})


class SelectLinkedTopicForm(forms.Form):
    topic = AutoCompleteSelectField('linked_topic_lookup',
                                    label='Find a topic (click to see it) ', help_text='')


class AddRelationAsymForm(forms.Form):
    A = AutoCompleteSelectField('topic_lookup', label='', help_text='')
    relation = forms.ChoiceField(choices=TOPIC_RELATIONS_ASYM, label='')
    B = AutoCompleteSelectField('topic_lookup', label='', help_text='')
