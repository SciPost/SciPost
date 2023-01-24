__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField

from ..models import Qualification, Readiness


class QualificationForm(forms.ModelForm):

    class Meta:
        model = Qualification
        fields = [
            "submission",
            "fellow",
            "expertise_level",
            # "comments",
        ]
        widgets = {
            "submission": forms.HiddenInput(),
            "fellow": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["expertise_level"].label = "Your expertise level for this Submission"
        self.helper.layout = Layout(
            Field("submission"),
            Field("fellow"),
            FloatingField("expertise_level"),
        )


class ReadinessForm(forms.ModelForm):
    choice = forms.ChoiceField(
        choices=(
            [('', '---------'), ("yes", "Yes, let me take charge now"),] +
            list(Readiness.STATUS_CHOICES)
        ),
    )

    class Meta:
        model = Readiness
        fields = [
            "submission",
            "fellow",
            "choice",
        ]
        widgets = {
            "submission": forms.HiddenInput(),
            "fellow": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs and kwargs["instance"]:
            self.fields["choice"].initial = kwargs["instance"].status
        self.helper = FormHelper()
        self.fields["choice"].label = "Ready to take charge?"

        self.helper.layout = Layout(
            Field("submission"),
            Field("fellow"),
            FloatingField("choice"),
        )

    def save(self):
        instance = super().save(commit=False)
        # The "yes" choice must be handled separately in the view before calling save
        instance.status = self.cleaned_data["choice"]
        instance.save()
        return instance
