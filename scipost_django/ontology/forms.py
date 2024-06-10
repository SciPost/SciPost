__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.utils import ProgrammingError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from .constants import TOPIC_RELATIONS_ASYM
from .models import Branch, AcademicField, Specialty, Tag, Topic


def academic_field_slug_choices():
    choices = (("All", (("all", "All"),)),)
    try:
        for branch in Branch.objects.all():
            if branch.name != "Multidisciplinary" and branch.journals.active().exists():
                subchoices = ()
                for acad_field in branch.academic_fields.all():
                    if acad_field.journals.active().exists():
                        subchoices += ((acad_field.slug, acad_field.name),)
                choices += ((branch.name, subchoices),)
    except ProgrammingError:  # when running on new, empty database
        pass
    return choices


class AcadFieldSpecialtyForm(forms.Form):
    """
    A form to select an academic field and its associated specialties.
    """

    acad_field_slug = forms.ChoiceField(
        label="Academic Field", choices=academic_field_slug_choices()
    )
    specialty_slug = forms.ChoiceField(label="Specialty", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Delete specialty_slug field from the form if acad_field_slug is not set
        acad_field_slug = self.data.get("acad_field_slug")
        if acad_field_slug is None or acad_field_slug == "all":
            del self.fields["specialty_slug"]
        else:
            self.set_specialty_choices()

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                FloatingField("specialty_slug", wrapper_class='mb-0'),
                FloatingField("acad_field_slug", wrapper_class='mb-0'),
                css_class="d-flex flex-row gap-2",
            )
        )

    def set_specialty_choices(self):
        acad_field_slug = self.data.get("acad_field_slug")
        specialties = (
            Specialty.objects.filter(acad_field__slug=acad_field_slug)
            if acad_field_slug
            else Specialty.objects.none()
        )
        self.fields["specialty_slug"].choices = [("all", "All specialties")] + [
            (specialty.slug, str(specialty)) for specialty in specialties.all()
        ]


class SessionAcademicFieldForm(forms.Form):
    acad_field_slug = forms.ChoiceField(
        label="Academic Field", choices=academic_field_slug_choices()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.show_errors = True
        self.helper.layout = Layout(Div(FloatingField("acad_field_slug")))


def specialty_slug_choices(acad_field_slug):
    specialties = (
        Specialty.objects.filter(acad_field__slug=acad_field_slug)
        if acad_field_slug
        else Specialty.objects.none()
    )
    choices = (("all", "All specialties"),)
    for specialty in specialties.all():
        choices += ((specialty.slug, str(specialty)),)
    return choices


class SessionSpecialtyForm(forms.Form):
    specialty_slug = forms.ChoiceField(
        label="Specialty",
    )

    def __init__(self, *args, **kwargs):
        try:
            acad_field_slug = kwargs.pop("acad_field_slug")
        except KeyError:
            acad_field_slug = ""
        super().__init__(*args, **kwargs)
        self.fields["specialty_slug"].choices = specialty_slug_choices(acad_field_slug)
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.show_errors = True
        self.helper.layout = Layout(Div(FloatingField("specialty_slug")))


class SelectTagsForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="/ontology/tag-autocomplete"),
        label="",
    )


class TopicForm(forms.ModelForm):
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        help_text="Type to search, click to include",
    )

    class Meta:
        model = Topic
        fields = [
            "specialties",
            "name",
            "slug",
            "tags",
        ]

    def save(self):
        instance = super().save()
        for specialty in self.cleaned_data["specialties"].all():
            specialty.topics.add(instance)
        return instance


class SelectTopicForm(forms.Form):
    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="/ontology/topic-autocomplete"),
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].widget.attrs.update(
            {"placeholder": "type here to find topic"}
        )


class TopicDynSelForm(forms.Form):
    q = forms.CharField(max_length=32, label="Search")
    action_url_name = forms.CharField()
    action_url_base_kwargs = forms.JSONField(required=False)
    action_target_element_id = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("q", autocomplete="off"),
            Field("action_url_name", type="hidden"),
            Field("action_url_base_kwargs", type="hidden"),
            Field("action_target_element_id", type="hidden"),
        )

    def search_results(self):
        if self.cleaned_data["q"]:
            topics = Topic.objects.filter(name__icontains=self.cleaned_data["q"])
            return topics
        else:
            return Topic.objects.none()


class SelectLinkedTopicForm(forms.Form):
    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/topic-linked-autocomplete", attrs={"data-html": True}
        ),
        label="Find a topic (click to see it)",
    )


class AddRelationAsymForm(forms.Form):
    A = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2(url="/ontology/topic-autocomplete"),
        label="",
    )
    relation = forms.ChoiceField(choices=TOPIC_RELATIONS_ASYM, label="")
    B = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=autocomplete.ModelSelect2(url="/ontology/topic-autocomplete"),
        label="",
    )
