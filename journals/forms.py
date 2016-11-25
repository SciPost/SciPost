from django import forms
from django.utils import timezone

from .models import SCIPOST_JOURNALS
from .models import UnregisteredAuthor, Issue, Publication

from submissions.models import Submission

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, Submit


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

# class InitiatePublicationForm(forms.ModelForm):
#     class Meta:
#         model = Publication
#         fields = ['accepted_submission',
#                   #'in_journal', 'volume', 'issue',
#                   'in_issue', 'paper_nr',
#                   'pdf_file',
#                   'submission_date', 'acceptance_date',
#         ]
#     # accepted_submission = forms.ModelChoiceField(
#     #     queryset=Submission.objects.filter(status='accepted'))
#     # in_journal = forms.ChoiceField(choices=SCIPOST_JOURNALS,)
#     # volume = forms.IntegerField()
#     # issue = forms.IntegerField()

#     def __init__(self, *args, **kwargs):
#         super(InitiatePublicationForm, self).__init__(*args, **kwargs)
#         self.fields['accepted_submission'] = forms.ModelChoiceField(
#             queryset=Submission.objects.filter(status='accepted'))
#         self.fields['accepted_submission'].label=''
#         #self.fields['in_journal'].label=''
#         #self.fields['journal'].label=''
#         #self.fields['volume'].label=''
#         #self.fields['issue'].label=''
#         self.fields['in_issue'].label=''
#         self.fields['paper_nr'].label=''
#         self.fields['acceptance_date'].label=''
#         self.fields['submission_date'].label=''
#         self.helper = FormHelper()
#         self.helper.layout = Layout(
#             Div(HTML('<h3>Which Submission is ready for publishing?</h3>'),
#                 Field('accepted_submission')),
#             # Div(HTML('<h3>In which Journal?</h3>'),
#             #     #Field('in_journal')),
#             #     Field('journal')),
#             # Div(HTML('<h3>Which Volume?</h3>'),
#             #     Field('volume')),
#             # Div(HTML('<h3>Which issue?</h3>'),
#             #     Field('issue')),
#              Div(HTML('<h3>Which Journal/Volume/Issue?</h3>'),
#                  Field('in_issue')),
#             Div(HTML('<h3>Which paper number?</h3>'),
#                 Field('paper_nr')),
#             Div(HTML('<h3>pdf file (post-proof stage):</h3>'),
#                 Field('pdf_file')),
#             Div(HTML('<h3>When was the paper originally submitted?</h3>'),
#                 Field('submission_date')),
#             Div(HTML('<h3>When was the paper accepted?</h3>'),
#                 Field('acceptance_date')),
#             Submit('submit', 'Initiate publication'),
#         )


class ValidatePublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        exclude = ['authors', 'authors_claims', 'authors_false_claims',
                   'metadata', 'metadata_xml',
                   'latest_activity',]


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
