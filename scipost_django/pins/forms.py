__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.contrib.contenttypes.models import ContentType

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = (
            "title",
            "description",
            "visibility",
            "author",
            "regarding_object_id",
            "regarding_content_type",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "author": forms.HiddenInput(),
            "regarding_object_id": forms.HiddenInput(),
            "regarding_content_type": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("description"), css_class="col-12"),
                Div(FloatingField("title"), css_class="col"),
                Div(FloatingField("visibility"), css_class="col-auto"),
                Submit("submit", "Submit", css_class="col-auto btn btn-sm mb-3"),
                css_class="row",
            ),
            # Hidden fields
            Field("author"),
            Field("regarding_object_id"),
            Field("regarding_content_type"),
        )

    def save_regarding_content_type(self, content_type):
        regarding_content_type = ContentType.objects.get_for_model(content_type)
        return regarding_content_type
