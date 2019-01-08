__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.forms import BaseModelFormSet, modelformset_factory

from django_countries import countries
from django_countries.fields import LazyTypedChoiceField
from django_countries.widgets import CountrySelectWidget

from common.widgets import DateWidget

from .models import Affiliation, Institution


class AffiliationForm(forms.ModelForm):
    name = forms.CharField(label='* Institution', max_length=300)
    country = LazyTypedChoiceField(
        choices=countries, label='* Country', widget=CountrySelectWidget(), initial='NL')

    class Meta:
        model = Affiliation
        fields = (
            'name',
            'country',
            'begin_date',
            'end_date',
        )
        widgets = {
            'begin_date': DateWidget(required=False),
            'end_date': DateWidget(required=False)
        }

    class Media:
        js = ('scipost/formset.js',)

    def __init__(self, *args, **kwargs):
        self.contributor = kwargs.pop('contributor')
        affiliation = kwargs.get('instance')
        if hasattr(affiliation, 'institution'):
            institution = affiliation.institution
            kwargs['initial'] = {
                'name': institution.name,
                'country': institution.country
            }
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Save the Affiliation and Institution if neccessary.
        """
        affiliation = super().save(commit=False)
        affiliation.contributor = self.contributor

        if commit:
            if hasattr(affiliation, 'institution') and affiliation.institution.affiliations.count() == 1:
                # Just update if there are no other people using this Institution
                institution = affiliation.institution
                institution.name = self.cleaned_data['name']
                institution.country = self.cleaned_data['country']
                institution.save()
            else:
                institution, __ = Institution.objects.get_or_create(
                    name=self.cleaned_data['name'],
                    country=self.cleaned_data['country'])
                affiliation.institution = institution
            affiliation.save()
        return affiliation


class BaseAffiliationsFormSet(BaseModelFormSet):
    """
    This formset helps update the Institutions for the Contributor at specific time periods.
    """
    def __init__(self, *args, **kwargs):
        self.contributor = kwargs.pop('contributor')
        super().__init__(*args, **kwargs)
        self.queryset = self.contributor.affiliations.all()

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['contributor'] = self.contributor
        return kwargs

    def save(self, commit=True):
        self.deleted_objects = []

        for form in self.forms:
            form.save(commit)

        # Delete Affiliations if needed
        for form in self.deleted_forms:
            self.deleted_objects.append(form.instance)
            self.delete_existing(form.instance, commit=commit)


AffiliationsFormset = modelformset_factory(Affiliation, form=AffiliationForm, can_delete=True,
                                           formset=BaseAffiliationsFormSet, extra=0)


class InstitutionMergeForm(forms.ModelForm):
    institution = forms.ModelChoiceField(queryset=Institution.objects.none())

    class Meta:
        model = Institution
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institution'].queryset = Institution.objects.exclude(id=self.instance.id)

    def save(self, commit=True):
        old_institution = self.cleaned_data['institution']
        if commit:
            Affiliation.objects.filter(
                institution=old_institution).update(institution=self.instance)
            old_institution.delete()
        return self.instance
