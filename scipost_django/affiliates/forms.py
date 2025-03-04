__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User
from django.forms import BaseModelFormSet, modelformset_factory
from django.utils.text import slugify

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, Submit

from dal import autocomplete

from affiliates.models.publisher import AffiliatePublisher
from scipost.services import DOICaller, extract_publication_date_from_Crossref_data

from organizations.models import Organization

from .models import (
    AffiliateJournal,
    AffiliateJournalYearSubsidy,
    AffiliatePublication,
    AffiliatePubFraction,
)

from .regexes import DOI_AFFILIATEPUBLICATION_REGEX


class AffiliateJournalForm(forms.ModelForm):
    """
    Form for creating or updating an AffiliateJournal.
    """

    publisher = forms.ChoiceField(
        choices=[(None, "---------"), ("create", "Create from journal name")]
    )

    class Meta:
        model = AffiliateJournal
        fields = [
            "publisher",
            "name",
            "description",
            "short_name",
            "slug",
            "acad_field",
            "specialties",
            "homepage",
            "logo_svg",
            "logo",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "specialties": autocomplete.ModelSelect2Multiple(
                url="/ontology/specialty-autocomplete"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["publisher"].choices += list(
            AffiliatePublisher.objects.values_list("id", "name")
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("publisher"),
            Fieldset(
                "Name / Description",
                Div(
                    Field("name"),
                    Field("short_name"),
                    Field("slug"),
                    css_class="col-12 col-md-auto",
                ),
                Div(Field("description"), css_class="col-12 col-md"),
                css_class="row",
            ),
            Fieldset(
                "Ontology",
                Div(Field("acad_field"), css_class="col"),
                Div(Field("specialties"), css_class="col"),
                css_class="row",
            ),
            Fieldset(
                "Branding",
                Div(Field("homepage"), css_class="col"),
                Div(Field("logo_svg"), css_class="col"),
                Div(Field("logo"), css_class="col"),
                css_class="row",
            ),
            Submit("submit", "Save"),
        )

    def clean_slug(self):
        input_slug = self.cleaned_data["slug"]
        sluggified = slugify(input_slug)
        if input_slug.lower() != sluggified.lower():
            raise forms.ValidationError(
                "The slug does not follow the correct format. "
                "The proper slug would be: "
                f"{sluggified}"
            )
        if (
            AffiliateJournal.objects.exclude(pk=self.instance.pk)
            .filter(slug=input_slug)
            .exists()
        ):
            raise forms.ValidationError("This slug is already in use.")
        return input_slug

    def clean(self):
        input_publisher = self.cleaned_data["publisher"]
        if input_publisher == "create":
            self.cleaned_data["publisher"] = AffiliatePublisher.objects.get_or_create(
                name=self.cleaned_data["name"]
            )[0]
        else:
            try:
                self.cleaned_data["publisher"] = AffiliatePublisher.objects.get(
                    id=input_publisher
                )
            except AffiliatePublisher.DoesNotExist:
                raise forms.ValidationError("The selected publisher does not exist.")


class AffiliateJournalManagerForm(AffiliateJournalForm):
    """
    A subset of the AffiliateJournalForm for journal managers,
    offering less fields to edit.
    """

    class Meta:
        model = AffiliateJournal
        fields = [
            "name",
            "description",
            "homepage",
        ]


class AffiliateJournalAddManagerForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/user-autocomplete", attrs={"data-html": True}
        ),
        label="",
        required=True,
    )


class AffiliateJournalSpecifyCostInfoForm(forms.Form):
    journal = forms.ModelChoiceField(
        queryset=AffiliateJournal.objects.all(),
        widget=forms.HiddenInput(),
    )
    year = forms.IntegerField()
    cost = forms.IntegerField(min_value=0)

    def save(self, *args, **kwargs):
        journal = self.cleaned_data["journal"]
        journal.cost_info[self.cleaned_data["year"]] = self.cleaned_data["cost"]
        journal.save()


class AffiliateJournalAddPublicationForm(forms.ModelForm):
    class Meta:
        model = AffiliatePublication
        fields = ["doi", "journal"]
        widgets = {
            "journal": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.crossref_data = {}
        self.publication_date = None
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        # Check that the journal specified in the DOI data is
        # the same as in the form
        if (
            self.crossref_data
            and self.crossref_data.get(
                "container-title",
                [
                    "",
                ],
            )[0]
            != self.cleaned_data["journal"].name
        ):
            raise forms.ValidationError(
                "The journal specified in the DOI is different."
            )
        return cleaned_data

    def clean_doi(self):
        input_doi = self.cleaned_data["doi"]
        if AffiliatePublication.objects.filter(doi=input_doi).exists():
            raise forms.ValidationError("This publication has already been added.")
        caller = DOICaller(input_doi)
        if caller.is_valid:
            self.crossref_data = DOICaller(input_doi).data["crossref_data"]
        else:
            error_message = "Could not find a resource for that DOI."
            raise forms.ValidationError(error_message)
        return input_doi

    def save(self, *args, **kwargs):
        self.instance.doi = self.cleaned_data["doi"]
        self.instance._metadata_crossref = self.crossref_data
        self.instance.journal = self.cleaned_data["journal"]
        self.instance.publication_date = extract_publication_date_from_Crossref_data(
            self.crossref_data
        )
        return super().save()


class AffiliatePublicationAddPubFractionForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        required=True,
    )

    class Meta:
        model = AffiliatePubFraction
        fields = ["organization", "publication", "fraction"]
        widgets = {"publication": forms.HiddenInput()}

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        # Verify that the organization does not already
        # have a PubFraction for this AffiliatePublication
        organization = cleaned_data["organization"]
        publication = cleaned_data["publication"]
        if publication.pubfractions.filter(organization=organization).exists():
            raise forms.ValidationError(
                "This Organization already has a PubFraction "
                "for this Publication.\nIf you want to change it, "
                "delete the existing one and re-add a new one."
            )
        return cleaned_data

    def clean_fraction(self):
        input_fraction = self.cleaned_data["fraction"]
        if input_fraction < 0:
            raise forms.ValidationError("The PubFraction cannot be negative!")
        elif input_fraction > 1:
            raise forms.ValidationError("An individual PubFraction cannot exceed 1!")
        return input_fraction


class AffiliateJournalAddYearSubsidyForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        required=True,
    )

    class Meta:
        model = AffiliateJournalYearSubsidy
        fields = [
            "journal",
            "organization",
            "description",
            "amount",
            "year",
        ]
        widgets = {"journal": forms.HiddenInput()}
