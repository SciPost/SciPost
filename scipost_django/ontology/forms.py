__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from dal import autocomplete

from .constants import TOPIC_RELATIONS_ASYM
from .models import Tag, Topic


class SelectTagsForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url='/ontology/tag-autocomplete'),
        label=''
    )

class SelectTopicForm(forms.Form):
    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url='/ontology/topic-autocomplete'),
        label=''
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic'].widget.attrs.update({
            'placeholder':'type here to find topic'})


class SelectLinkedTopicForm(forms.Form):
    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='/ontology/topic-linked-autocomplete',
            attrs={'data-html': True}
        ),
        label='Find a topic (click to see it)'
    )


class AddRelationAsymForm(forms.Form):
    A = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2(url='/ontology/topic-autocomplete'),
        label=''
    )
    relation = forms.ChoiceField(choices=TOPIC_RELATIONS_ASYM, label='')
    B = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2(url='/ontology/topic-autocomplete'),
        label=''
    )
