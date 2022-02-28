__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from .models import WebinarRegistration

from organizations.models import Organization
from scipost.fields import ReCaptchaField


class WebinarRegistrationForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        required=False,
    )
    captcha = ReCaptchaField(label="* Please verify to continue:")

    class Meta:
        model = WebinarRegistration
        fields = [
            "webinar",
            "first_name",
            "last_name",
            "email",
            "organization",
            "affiliation",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["affiliation"].help_text = "if you don't find your Organization"
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("webinar", type="hidden"),
            Div(
                Div(FloatingField("first_name"), css_class="col-lg-6"),
                Div(FloatingField("last_name"), css_class="col-lg-6"),
                css_class="row"
            ),
            Div(
                Div(
                    Div(
                        Field("organization"),
                        Field("affiliation"),
                    ),
                    css_class="col-lg-6"
                ),
                Div(
                    FloatingField("email"),
                    Field("captcha"),
                    ButtonHolder(
                        Submit(
                            "submit", "Register", css_class="btn btn-success float-end"
                        )
                    ),
                    css_class="col-lg-6"
                ),
                css_class="row"
            )
        )
