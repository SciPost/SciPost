from django import forms
from django.shortcuts import get_object_or_404

from .models import Commentary

from scipost.models import Contributor

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
    existing_commentary = None

    class Meta:
        model = Commentary
        fields = ['type', 'discipline', 'domain', 'subject_area',
                  'pub_title', 'author_list',
                  'metadata',
                  'journal', 'volume', 'pages', 'pub_date',
                  'arxiv_identifier',
                  'pub_DOI', 'pub_abstract']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(RequestCommentaryForm, self).__init__(*args, **kwargs)
        self.fields['metadata'].widget = forms.HiddenInput()
        self.fields['pub_date'].widget.attrs.update({'placeholder': 'Format: YYYY-MM-DD'})
        self.fields['arxiv_identifier'].widget.attrs.update(
            {'placeholder': 'ex.:  1234.56789v1 or cond-mat/1234567v1'})
        self.fields['pub_DOI'].widget.attrs.update({'placeholder': 'ex.: 10.21468/00.000.000000'})
        self.fields['pub_abstract'].widget.attrs.update({'cols': 100})

    def clean(self, *args, **kwargs):
        cleaned_data = super(RequestCommentaryForm, self).clean(*args, **kwargs)

        # Either Arxiv-ID or DOI is given
        if not cleaned_data['arxiv_identifier'] and not cleaned_data['pub_DOI']:
            msg = ('You must provide either a DOI (for a published paper) '
                'or an arXiv identifier (for a preprint).')
            self.add_error('arxiv_identifier', msg)
            self.add_error('pub_DOI', msg)
        elif (cleaned_data['arxiv_identifier'] and
              (Commentary.objects
               .filter(arxiv_identifier=cleaned_data['arxiv_identifier']).exists())):
            msg = 'There already exists a Commentary Page on this preprint, see'
            self.existing_commentary = get_object_or_404(
                Commentary,
                arxiv_identifier=cleaned_data['arxiv_identifier'])
            self.add_error('arxiv_identifier', msg)
        elif (cleaned_data['pub_DOI'] and
              Commentary.objects.filter(pub_DOI=cleaned_data['pub_DOI']).exists()):
            msg = 'There already exists a Commentary Page on this publication, see'
            self.existing_commentary = get_object_or_404(Commentary, pub_DOI=cleaned_data['pub_DOI'])
            self.add_error('pub_DOI', msg)

        # Current user is not known
        if not self.user or not Contributor.objects.filter(user=self.user).exists():
            self.add_error(None, 'Sorry, current user is not known to SciPost.')


    def save(self, *args, **kwargs):
        """Prefill instance before save"""
        self.requested_by = Contributor.objects.get(user=self.user)
        return super(RequestCommentaryForm, self).save(*args, **kwargs)

    def get_existing_commentary(self):
        """Get Commentary if found after validation"""
        return self.existing_commentary


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
