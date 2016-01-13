from django import forms

from .models import *


class SubmissionForm(forms.Form):
    submitted_to_journal = forms.ChoiceField(choices=SCIPOST_JOURNALS_SUBMIT, required=True, label='SciPost Journal to submit to:')
    domain = forms.ChoiceField(choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = forms.ChoiceField(choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    title = forms.CharField(max_length=300, required=True, label='Title')
    author_list = forms.CharField(max_length=1000, required=True)
    abstract = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':60}), label='Abstract', required=True) # need TextField but doesn't exist
    arxiv_link = forms.URLField(label='arXiv link (including version nr)', required=True)

class ProcessSubmissionForm(forms.Form):
    editor_in_charge = forms.ModelChoiceField(queryset=Contributor.objects.filter(rank__gte=3), required=True)

class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")

