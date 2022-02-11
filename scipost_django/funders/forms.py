__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import Funder, Grant

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
        widget=autocomplete.ModelSelect2(
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
            widget=autocomplete.ModelSelect2(
                url="/funders/funder-autocomplete", attrs={"data-html": True}
            ),
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
        widget=autocomplete.ModelSelect2(
            url="/funders/grant-autocomplete", attrs={"data-html": True}
        ),
    )
