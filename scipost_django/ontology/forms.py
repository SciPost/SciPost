__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from .constants import TOPIC_RELATIONS_ASYM
from .models import AcademicField, Tag, Topic


class SessionAcademicFieldForm(forms.Form):
    acad_field = forms.ModelChoiceField(
        queryset=AcademicField.objects.all(),
        label='Academic Field'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.show_errors = True
        self.helper.layout = Layout(
            Div(FloatingField('acad_field'))
        )


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
