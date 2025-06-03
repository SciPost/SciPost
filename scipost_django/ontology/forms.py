__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.db.utils import ProgrammingError
from django.db.models import Q, Exists, OuterRef, Count
from django.urls import reverse_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from common.forms import HTMXDynSelWidget
from ontology.models.topic import TopicInterest
from profiles.models import Profile

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
                FloatingField("specialty_slug", wrapper_class="mb-0"),
                FloatingField("acad_field_slug", wrapper_class="mb-0"),
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


class SpecialtyInlineForm(forms.Form):
    """
    Form to select a specialty.
    """

    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        widget=HTMXDynSelWidget(
            url=reverse_lazy("ontology:specialty_dynsel"),
        ),
        label="",
    )

    def __init__(self, *args, **kwargs):
        submission = kwargs.pop("submission", None)

        super().__init__(*args, **kwargs)

        # If a submission is passed, limit the choices to the specialties of its target journal
        if submission:
            self.fields["specialty"].queryset = (
                submission.submitted_to.specialties.all()
            )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(Field("specialty")),
                Submit("add", "Add", css_class="mt-2 mb-3"),
                css_class="d-flex gap-2",
            )
        )


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
        help_texts = {
            "slug": "A unique identifier for the topic, used in URLs.",
            "tags": "Tags are used to categorize topics. Select all that apply.",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "e.g. Quantum Field Theory (QFT)"}
            ),
            "slug": forms.TextInput(
                attrs={"placeholder": "e.g. quantum-field-theory"},
            ),
            "tags": forms.CheckboxSelectMultiple(),
        }

    def save(self):
        instance = super().save()
        for specialty in self.cleaned_data["specialties"].all():
            specialty.topics.add(instance)
        return instance


class TopicInterestForm(forms.ModelForm):
    class Meta:
        model = TopicInterest
        fields = ["topic", "weight"]

        widgets = {
            "topic": HTMXDynSelWidget(url=reverse_lazy("ontology:topic_dynsel")),
            "weight": forms.NumberInput(
                attrs={"step": 0.1, "min": -1, "max": 1, "value": 1}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")

        if not isinstance(self.profile, Profile):
            raise ValueError("Profile object is required for this form.")

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        # self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(Field("topic"), css_class="col"),
                Div(Field("weight"), css_class="col-auto"),
                Div(Field("id", type="hidden"), css_class="d-none"),
                css_class="row mb-0",
            )
        )

    def save(self, commit=True):
        instance = self.cleaned_data.get("id")
        topic = self.cleaned_data.get("topic")
        weight = self.cleaned_data.get("weight")

        if not commit:
            return TopicInterest(
                profile=self.profile,
                topic=topic,
                weight=weight,
            )

        interest, created = TopicInterest.objects.update_or_create(
            profile=self.profile,
            topic=topic,
            source=TopicInterest.SOURCE_MANUAL,  # Force manual source
            defaults={"weight": weight},
        )

        return interest


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


class TopicSearchForm(forms.Form):
    q = forms.CharField(
        max_length=256,
        label="Search",
        required=False,
    )

    acad_fields = forms.ModelMultipleChoiceField(
        queryset=AcademicField.objects.all(),
        required=False,
    )

    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        required=False,
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("name", "Name"),
            ("nr_submissions", "# submissions"),
            ("nr_publications", "# publications"),
        ),
        initial="name",
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            ("+", "Ascending"),
            ("-", "Descending"),
        ),
        initial="+",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Div(
                Div(Field("q"), css_class="col-12 col-md-8"),
                Div(
                    Div(
                        Div(Field("orderby"), css_class="col-12 col-md-6"),
                        Div(Field("ordering"), css_class="col-12 col-md-6"),
                        css_class="row mb-0",
                    ),
                    css_class="col-12 col-md-4",
                ),
                Div(Field("acad_fields", size=6), css_class="col-12 col-md"),
                Div(Field("specialties", size=6), css_class="col-12 col-md"),
                Div(Field("tags", size=6), css_class="col-12 col-md"),
                css_class="row mb-0",
            ),
        )

    def search_results(self):
        objects = Topic.objects.all().annotate(
            nr_submissions=Count("submission", distinct=True),
            nr_publications=Count("publications", distinct=True),
        )

        if q := self.cleaned_data.get("q"):
            objects = objects.filter(
                Q(name__unaccent__icontains=q) | Q(slug__unaccent__icontains=q)
            )

        if acad_fields := self.cleaned_data.get("acad_fields"):
            objects = objects.annotate(
                belongs_to_acad_field=Exists(
                    Specialty.objects.filter(
                        acad_field__in=acad_fields,
                        topics=OuterRef("pk"),
                    )
                )
            ).filter(belongs_to_acad_field=True)

        if specialties := self.cleaned_data.get("specialties"):
            objects = objects.filter(specialties__in=specialties)

        if tags := self.cleaned_data.get("tags"):
            objects = objects.filter(tags__in=tags)

        # Ordering of objects
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            objects = objects.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        objects = objects.prefetch_related(
            "specialties",
            "tags",
        )

        return objects


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
