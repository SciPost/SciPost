__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.contrib.auth.models import User
from django.forms import BaseModelFormSet, modelformset_factory

from dal import autocomplete

from scipost.services import (
    DOICaller,
    extract_publication_date_from_Crossref_data)

from organizations.models import Organization

from .models import AffiliatePublication, AffiliatePubFraction
from .regexes import DOI_AFFILIATEPUBLICATION_REGEX


class AffiliateJournalAddManagerForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/user-autocomplete',
            attrs={'data-html': True}
        ),
        label='',
        required=True
    )


class AffiliateJournalAddPublicationForm(forms.ModelForm):
    class Meta:
        model = AffiliatePublication
        fields = [
            'doi',
            'journal'
        ]
        widgets = {
            'journal': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.crossref_data = {}
        self.publication_date = None
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        # Check that the journal specified in the DOI data is
        # the same as in the form
        if (self.crossref_data and
            self.crossref_data.get('container-title', ['',])[0] !=
            self.cleaned_data['journal'].name):
            raise forms.ValidationError(
                'The journal specified in the DOI is different.')
        return cleaned_data

    def clean_doi(self):
        input_doi = self.cleaned_data['doi']
        if AffiliatePublication.objects.filter(
                doi=input_doi).exists():
            raise forms.ValidationError(
                'This publication has already been added.')
        caller = DOICaller(input_doi)
        if caller.is_valid:
            self.crossref_data = DOICaller(input_doi).data['crossref_data']
        else:
            error_message = 'Could not find a resource for that DOI.'
            raise forms.ValidationError(error_message)
        return input_doi

    def save(self, *args, **kwargs):
        self.instance.doi = self.cleaned_data['doi']
        self.instance._metadata_crossref = self.crossref_data
        self.instance.journal = self.cleaned_data['journal']
        self.instance.publication_date = extract_publication_date_from_Crossref_data(self.crossref_data)
        return super().save()


class AffiliatePublicationAddPubFractionForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='/organizations/organization-autocomplete',
            attrs={'data-html': True}
        ),
        required=True
    )
    class Meta:
        model = AffiliatePubFraction
        fields = [
            'organization',
            'publication',
            'fraction'
        ]
        widgets = {
            'publication': forms.HiddenInput()
        }

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        # Verify that the organization does not already
        # have a PubFraction for this AffiliatePublication
        organization = cleaned_data['organization']
        publication = cleaned_data['publication']
        if publication.pubfractions.filter(
                organization=organization).exists():
            raise forms.ValidationError(
                'This Organization already has a PubFraction '
                'for this Publication.\nIf you want to change it, '
                'delete the existing one and re-add a new one.')
        return cleaned_data

    def clean_fraction(self):
        input_fraction = self.cleaned_data['fraction']
        if input_fraction < 0:
            raise forms.ValidationError(
                'The PubFraction cannot be negative!')
        elif input_fraction > 1:
            raise forms.ValidationError(
                'An individual PubFraction cannot exceed 1!')
        return input_fraction
