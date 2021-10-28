__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from .constants import TOPIC_RELATIONS_ASYM
from .models import Branch, AcademicField, Specialty, Tag, Topic


def academic_field_slug_choices():
    choices = (
        ('All', (
            ('all', 'All'),
        )),
    )
    for branch in Branch.objects.all():
        if branch.name != 'Multidisciplinary' and branch.journals.active().exists():
            subchoices = ()
            for acad_field in branch.academic_fields.all():
                if acad_field.journals.active().exists():
                    subchoices += (
                        (acad_field.slug, acad_field.name),
                    )
            choices += (
                (branch.name, subchoices),
            )
    return choices


class SessionAcademicFieldForm(forms.Form):
    acad_field_slug = forms.ChoiceField(
        label='Academic Field',
        choices=academic_field_slug_choices()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.show_errors = True
        self.helper.layout = Layout(
            Div(FloatingField('acad_field_slug'))
        )


def specialty_slug_choices(acad_field_slug):
    specialties = Specialty.objects.filter(
        acad_field__slug=acad_field_slug) if acad_field_slug else Specialty.objects.none()
    choices = (
        ('', '--------'),
    )
    for specialty in specialties.all():
        choices += ((specialty.slug, str(specialty)),)
    return choices


class SessionSpecialtyForm(forms.Form):
    specialty_slug = forms.ChoiceField(
        label='Specialty',
    )

    def __init__(self, *args, **kwargs):
        try:
            acad_field_slug = kwargs.pop('acad_field_slug')
        except KeyError:
            acad_field_slug = ''
        super().__init__(*args, **kwargs)
        self.fields['specialty_slug'].choices = specialty_slug_choices(acad_field_slug)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.show_errors = True
        self.helper.layout = Layout(
            Div(FloatingField('specialty_slug'))
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
