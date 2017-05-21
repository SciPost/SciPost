from django import forms
from django.utils import timezone

from .models import UnregisteredAuthor, Issue, Publication

from submissions.models import Submission



class InitiatePublicationForm(forms.Form):
    accepted_submission = forms.ModelChoiceField(
        queryset=Submission.objects.filter(status='accepted'))
    original_submission_date = forms.DateField()
    acceptance_date = forms.DateField()
    to_be_issued_in = forms.ModelChoiceField(
        queryset=Issue.objects.filter(until_date__gt=timezone.now()))

    def __init__(self, *args, **kwargs):
        super(InitiatePublicationForm, self).__init__(*args, **kwargs)
        self.fields['original_submission_date'].widget.attrs.update(
            {'placeholder': 'YYYY-MM-DD'})
        self.fields['acceptance_date'].widget.attrs.update(
            {'placeholder': 'YYYY-MM-DD'})


class ValidatePublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        exclude = ['authors', 'authors_claims', 'authors_false_claims',
                   'metadata', 'metadata_xml',
                   'latest_activity', ]


class UnregisteredAuthorForm(forms.ModelForm):
    class Meta:
        model = UnregisteredAuthor
        fields = ['first_name', 'last_name']


class CitationListBibitemsForm(forms.Form):
    latex_bibitems = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(CitationListBibitemsForm, self).__init__(*args, **kwargs)
        self.fields['latex_bibitems'].widget.attrs.update(
            {'rows': 30, 'cols': 50, 'placeholder': 'Paste the .tex bibitems here'})


class FundingInfoForm(forms.Form):
    funding_statement = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(FundingInfoForm, self).__init__(*args, **kwargs)
        self.fields['funding_statement'].widget.attrs.update(
            {'rows': 10, 'cols': 50,
             'placeholder': 'Paste the funding info statement here'})


class CreateMetadataXMLForm(forms.Form):
    metadata_xml = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(CreateMetadataXMLForm, self).__init__(*args, **kwargs)
        self.fields['metadata_xml'].widget.attrs.update(
            {'rows': 50, 'cols': 50, })
