from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
# from django.db.models import F

from django_countries import countries
from django_countries.fields import LazyTypedChoiceField
from django_countries.widgets import CountrySelectWidget

from common.widgets import DateWidget

from .models import Affiliation, Institution


class AffiliationForm(forms.ModelForm):
    name = forms.CharField(label='* Affiliation', max_length=300)
    country = LazyTypedChoiceField(
        choices=countries, label='* Country', widget=CountrySelectWidget())

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
        if hasattr(affiliation, 'institute'):
            institute = affiliation.institute
            kwargs['initial'] = {
                'name': institute.name,
                'country': institute.country
            }
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Save the Affiliation and Institute if neccessary.
        """
        affiliation = super().save(commit=False)
        affiliation.contributor = self.contributor

        if commit:
            if hasattr(affiliation, 'institute') and affiliation.institute.affiliations.count() == 1:
                # Just update if there are no other people using this Institute
                institute = affiliation.institute
                institute.name = self.cleaned_data['name']
                institute.country = self.cleaned_data['country']
                institute.save()
            else:
                institute, __ = Institution.objects.get_or_create(
                    name=self.cleaned_data['name'],
                    country=self.cleaned_data['country'])
                affiliation.institute = institute
            affiliation.save()
        return affiliation


class AffiliationsFormSet(BaseModelFormSet):
    """
    This formset helps update the Institutes for the Contributor at specific time periods.
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
                                           formset=AffiliationsFormSet, extra=0)


class InstituteMergeForm(forms.ModelForm):
    institute = forms.ModelChoiceField(queryset=Institution.objects.none())

    class Meta:
        model = Institution
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institute'].queryset = Institution.objects.exclude(id=self.instance.id)

    def save(self, commit=True):
        old_institute = self.cleaned_data['institute']
        if commit:
            Affiliation.objects.filter(institute=old_institute).update(institute=self.instance)
            old_institute.delete()
        return self.instance
