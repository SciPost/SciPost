from django import forms

from .models import Commentary

COMMENTARY_ACTION_CHOICES = (
    (0, 'modify'),
    (1, 'accept'),
    (2, 'refuse (give reason below)'),
    )

COMMENTARY_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'a commentary on this paper already exists'),
    (-2, 'this paper cannot be traced'),
    (-3, 'there exists a more revent version of this arXiv preprint'),
    )
commentary_refusal_dict = dict(COMMENTARY_REFUSAL_CHOICES)


class DOIToQueryForm(forms.Form):
    doi = forms.CharField(widget=forms.TextInput(
        {'label': 'DOI', 'placeholder': 'ex.: 10.21468/00.000.000000'}))


class IdentifierToQueryForm(forms.Form):
    identifier = forms.CharField(widget=forms.TextInput(
        {'label': 'arXiv identifier',
         'placeholder': 'new style ####.####(#)v# or old-style e.g. cond-mat/#######'}))


class RequestCommentaryForm(forms.ModelForm):
    class Meta:
        model = Commentary
        fields = ['type', 'discipline', 'domain', 'subject_area',
                  'pub_title', 'author_list',
                  'metadata',
                  'journal', 'volume', 'pages', 'pub_date',
                  'arxiv_identifier',
                  'pub_DOI', 'pub_abstract']

    def __init__(self, *args, **kwargs):
        super(RequestCommentaryForm, self).__init__(*args, **kwargs)
        self.fields['metadata'].widget = forms.HiddenInput()
        self.fields['pub_date'].widget.attrs.update({'placeholder': 'Format: YYYY-MM-DD'})
        self.fields['arxiv_identifier'].widget.attrs.update(
            {'placeholder': 'ex.:  1234.56789v1 or cond-mat/1234567v1'})
        self.fields['pub_DOI'].widget.attrs.update({'placeholder': 'ex.: 10.21468/00.000.000000'})
        self.fields['pub_abstract'].widget.attrs.update({'cols': 100})

class VetCommentaryForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=COMMENTARY_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENTARY_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

class CommentarySearchForm(forms.Form):
    """Search for Commentary specified by user"""
    pub_author = forms.CharField(max_length=100, required=False, label="Author(s)")
    pub_title_keyword = forms.CharField(max_length=100, required=False, label="Title")
    pub_abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")

    def search_results(self):
        """Return all Commentary objects according to search"""
        return Commentary.objects.vetted(
            pub_title__icontains=self.cleaned_data['pub_title_keyword'],
            pub_abstract__icontains=self.cleaned_data['pub_abstract_keyword'],
            author_list__icontains=self.cleaned_data['pub_author']).order_by('-pub_date')
