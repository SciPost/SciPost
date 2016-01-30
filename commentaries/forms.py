from django import forms

from .models import *

COMMENTARY_ACTION_CHOICES = (
    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
    )

COMMENTARY_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'a commentary on this paper already exists'),
    (-2, 'this paper cannot be traced'),
    (-3, 'this arXiv preprint is too recent (< 8 weeks)'),
    )

#class RequestCommentaryForm(forms.Form):
#    type = forms.ChoiceField(choices=COMMENTARY_TYPES)
#    pub_title = forms.CharField(max_length=300, label="Title")
#    author_list = forms.CharField(max_length=1000)
#    pub_date = forms.DateField(label="Publication date (YYYY-MM-DD)")
#    arxiv_link = forms.URLField(label='arXiv link (including version nr)', required=False)
#    pub_DOI_link = forms.URLField(label='DOI link to the published version', required=False)
#    pub_abstract = forms.CharField(widget=forms.Textarea, label="Abstract") # need TextField but doesn't exist
class RequestCommentaryForm(forms.ModelForm):
    class Meta:
        model = Commentary
        fields = ['type', 'discipline', 'pub_title', 'author_list', 'pub_date', 'arxiv_link', 'pub_DOI_link', 'pub_abstract']

    def __init__(self, *args, **kwargs):
        super(RequestCommentaryForm, self).__init__(*args, **kwargs)
        self.fields['pub_date'].widget.attrs.update({'placeholder': 'Format: YYYY-MM-DD'})
        self.fields['arxiv_link'].widget.attrs.update({'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})
        self.fields['pub_DOI_link'].widget.attrs.update({'placeholder': 'ex.: dx.doi.org/10.1103/PhysRevLett.000.000000'})
    
class VetCommentaryForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=COMMENTARY_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENTARY_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

class CommentarySearchForm(forms.Form):
    pub_author = forms.CharField(max_length=100, required=False, label="Author(s)")
    pub_title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    pub_abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")
