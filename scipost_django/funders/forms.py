__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.urls import reverse_lazy

from common.forms import HTMXDynSelWidget

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit

from .models import Funder, Grant, IndividualBudget

from dal import autocomplete

from scipost.forms import HttpRefererFormMixin
from scipost.models import Contributor
from organizations.models import Organization

from .models import Funder, Grant


class FunderRegistrySearchForm(forms.Form):
    name = forms.CharField(max_length=128)


class FunderForm(forms.ModelForm):
    class Meta:
        model = Funder
        fields = ["name", "acronym", "identifier"]


class FunderSelectForm(forms.Form):
    funder = forms.ModelChoiceField(
        queryset=Funder.objects.all(),
        widget=HTMXDynSelWidget(
            url="/funders/funder-autocomplete", attrs={"data-html": True}
        ),
    )


class FunderOrganizationSelectForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
    )

    class Meta:
        model = Funder
        fields = []


class GrantForm(HttpRefererFormMixin, forms.ModelForm):
    class Meta:
        model = Grant
        fields = ["funder", "number", "recipient_name", "recipient", "further_details"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["funder"] = forms.ModelChoiceField(
            queryset=Funder.objects.all(),
            widget=HTMXDynSelWidget(url="/funders/funder-autocomplete"),
        )
        self.fields["recipient"] = forms.ModelChoiceField(
            queryset=Contributor.objects.select_related("user").order_by(
                "user__last_name"
            ),
            required=False,
        )


class GrantSelectForm(forms.Form):
    grant = forms.ModelChoiceField(
        queryset=Grant.objects.all(),
        widget=HTMXDynSelWidget(url="/funders/grant-autocomplete"),
    )


class IndividualBudgetForm(forms.ModelForm):
    required_css_class = "required-asterisk"

    class Meta:
        model = IndividualBudget
        fields = [
            "organization",
            "description",
            "holder",
            "budget_number",
            "fundref_id",
        ]
        widgets = {
            "organization": autocomplete.ModelSelect2(
                url=reverse_lazy("organizations:organization-autocomplete"),
                attrs={
                    "data-html": True,
                    "style": "width: 100%",
                },
            ),
            "holder": autocomplete.ModelSelect2(
                url=reverse_lazy("profiles:profile-autocomplete"),
                attrs={
                    "data-html": True,
                    "style": "width: 100%",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("organization"), css_class="col-12 col-md-6"),
                Div(Field("holder"), css_class="col-12 col-md-6"),
                Div(Field("description"), css_class="col-12"),
                Div(Field("budget_number"), css_class="col-12 col-md"),
                Div(Field("fundref_id"), css_class="col-12 col-md"),
                css_class="row",
            ),
            ButtonHolder(Submit("submit", "Submit", css_class="btn-sm")),
        )
