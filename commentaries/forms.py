import re

from django import forms
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Commentary
from .constants import COMMENTARY_PUBLISHED, COMMENTARY_PREPRINT

from scipost.services import DOICaller, ArxivCaller
from scipost.models import Contributor

import strings


class DOIToQueryForm(forms.Form):
    VALID_DOI_REGEXP = r'^(?i)10.\d{4,9}/[-._;()/:A-Z0-9]+$'
    doi = forms.RegexField(regex=VALID_DOI_REGEXP, strip=True, help_text=strings.doi_query_help_text,
        error_messages={'invalid': strings.doi_query_invalid},
        widget=forms.TextInput({'label': 'DOI', 'placeholder': strings.doi_query_placeholder}))

    def clean_doi(self):
        input_doi = self.cleaned_data['doi']

        if Commentary.objects.filter(pub_DOI=input_doi).exists():
            error_message = 'There already exists a Commentary Page on this publication.'
            raise forms.ValidationError(error_message)

        caller = DOICaller(input_doi)
        if caller.is_valid:
            self.crossref_data = DOICaller(input_doi).data
        else:
            error_message = 'Could not find a resource for that DOI.'
            raise forms.ValidationError(error_message)

        return input_doi

    def request_published_article_form_prefill_data(self):
        additional_form_data = {'pub_DOI': self.cleaned_data['doi']}
        return {**self.crossref_data, **additional_form_data}


class ArxivQueryForm(forms.Form):
    IDENTIFIER_PATTERN_NEW = r'^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$'
    IDENTIFIER_PATTERN_OLD = r'^[-.a-z]+/[0-9]{7,}v[0-9]{1,2}$'
    VALID_ARXIV_IDENTIFIER_REGEX = "(?:{})|(?:{})".format(IDENTIFIER_PATTERN_NEW, IDENTIFIER_PATTERN_OLD)

    identifier = forms.RegexField(regex=VALID_ARXIV_IDENTIFIER_REGEX, strip=True,
        help_text=strings.arxiv_query_help_text, error_messages={'invalid': strings.arxiv_query_invalid},
        widget=forms.TextInput( {'placeholder': strings.arxiv_query_placeholder}))

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']

        if Commentary.objects.filter(arxiv_identifier=identifier).exists():
            error_message = 'There already exists a Commentary Page on this arXiv preprint.'
            raise forms.ValidationError(error_message)

        caller = ArxivCaller(identifier)
        if caller.is_valid:
            self.arxiv_data = ArxivCaller(identifier).data
        else:
            error_message = 'Could not find a resource for that arXiv identifier.'
            raise forms.ValidationError(error_message)

        return identifier

    def request_arxiv_preprint_form_prefill_data(self):
        additional_form_data = {'arxiv_identifier': self.cleaned_data['identifier']}
        return {**self.arxiv_data, **additional_form_data}


class RequestCommentaryForm(forms.ModelForm):
    class Meta:
        model = Commentary
        fields = [
            'discipline', 'domain', 'subject_area', 'pub_title', 'author_list', 'pub_date', 'pub_abstract'
        ]
        placeholders = {
            'pub_date': 'Format: YYYY-MM-DD'
        }


class RequestArxivPreprintForm(RequestCommentaryForm):
    class Meta(RequestCommentaryForm.Meta):
        model = Commentary
        fields = RequestCommentaryForm.Meta.fields + ['arxiv_identifier']

    def __init__(self, *args, **kwargs):
        super(RequestArxivPreprintForm, self).__init__(*args, **kwargs)
        # We want arxiv_identifier to be a required field.
        # Since it can be blank on the model, we have to override this property here.
        self.fields['arxiv_identifier'].required = True

    # TODO: add regex here?
    def clean_arxiv_identifier(self):
        arxiv_identifier = self.cleaned_data['arxiv_identifier']

        if Commentary.objects.filter(arxiv_identifier=arxiv_identifier).exists():
            error_message = 'There already exists a Commentary Page on this arXiv preprint.'
            raise forms.ValidationError(error_message)

        return arxiv_identifier

    def save(self, *args, **kwargs):
        self.instance.type = COMMENTARY_PREPRINT
        return super(RequestArxivPreprintForm, self).save(*args, **kwargs)


class RequestPublishedArticleForm(RequestCommentaryForm):
    class Meta(RequestCommentaryForm.Meta):
        fields = RequestCommentaryForm.Meta.fields + ['journal', 'volume', 'pages', 'pub_DOI']
        placeholders = {**RequestCommentaryForm.Meta.placeholders,
            **{'pub_DOI': 'ex.: 10.21468/00.000.000000'}}

    def __init__(self, *args, **kwargs):
        super(RequestPublishedArticleForm, self).__init__(*args, **kwargs)
        # We want pub_DOI to be a required field.
        # Since it can be blank on the model, we have to override this property here.
        self.fields['pub_DOI'].required = True

    def clean_pub_DOI(self):
        input_doi = self.cleaned_data['pub_DOI']

        if Commentary.objects.filter(pub_DOI=input_doi).exists():
            error_message = 'There already exists a Commentary Page on this publication.'
            raise forms.ValidationError(error_message)

        return input_doi

    def save(self, *args, **kwargs):
        self.instance.type = COMMENTARY_PUBLISHED
        return super(RequestPublishedArticleForm, self).save(*args, **kwargs)


class VetCommentaryForm(forms.Form):
    """Process an unvetted Commentary request.

    This form will provide fields to let the user
    process a Commentary that is unvetted. On success,
    the Commentary is either accepted or deleted from
    the database.

    Keyword arguments:
    commentary_id -- the Commentary.id to process (required)
    user -- User instance of the vetting user (required)

    """
    ACTION_MODIFY = 0
    ACTION_ACCEPT = 1
    ACTION_REFUSE = 2
    COMMENTARY_ACTION_CHOICES = (
        (ACTION_MODIFY, 'modify'),
        (ACTION_ACCEPT, 'accept'),
        (ACTION_REFUSE, 'refuse (give reason below)'),
    )
    REFUSAL_EMPTY = 0
    REFUSAL_PAPER_EXISTS = -1
    REFUSAL_UNTRACEBLE = -2
    REFUSAL_ARXIV_EXISTS = -3
    COMMENTARY_REFUSAL_CHOICES = (
        (REFUSAL_EMPTY, '-'),
        (REFUSAL_PAPER_EXISTS, 'a commentary on this paper already exists'),
        (REFUSAL_UNTRACEBLE, 'this paper cannot be traced'),
        (REFUSAL_ARXIV_EXISTS, 'there exists a more revent version of this arXiv preprint'),
    )
    COMMENTARY_REFUSAL_DICT = dict(COMMENTARY_REFUSAL_CHOICES)

    action_option = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=COMMENTARY_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=COMMENTARY_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

    def __init__(self, *args, **kwargs):
        """Pop and save keyword arguments if set, return form instance"""
        self.commentary_id = kwargs.pop('commentary_id', None)
        self.user = kwargs.pop('user', None)
        self.is_cleaned = False
        return super(VetCommentaryForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Check valid form and keyword arguments given"""
        cleaned_data = super(VetCommentaryForm, self).clean(*args, **kwargs)

        # Check valid `commentary_id`
        if not self.commentary_id:
            self.add_error(None, 'No `commentary_id` provided')
            return cleaned_data
        else:
            self.commentary = Commentary.objects.select_related('requested_by__user').get(
                pk=self.commentary_id)

        # Check valid `user`
        if not self.user:
            self.add_error(None, 'No `user` provided')
            return cleaned_data

        self.is_cleaned = True
        return cleaned_data

    def _form_is_cleaned(self):
        """Raise ValueError if form isn't validated"""
        if not self.is_cleaned:
            raise ValueError(('VetCommentaryForm could not be processed '
                              'because the data didn\'t validate'))

    def get_commentary(self):
        """Return Commentary if available"""
        self._form_is_cleaned()
        return self.commentary

    def get_refusal_reason(self):
        """Return refusal reason"""
        if self.commentary_is_refused():
            return self.COMMENTARY_REFUSAL_DICT[int(self.cleaned_data['refusal_reason'])]

    def commentary_is_accepted(self):
        self._form_is_cleaned()
        return int(self.cleaned_data['action_option']) == self.ACTION_ACCEPT

    def commentary_is_modified(self):
        self._form_is_cleaned()
        return int(self.cleaned_data['action_option']) == self.ACTION_MODIFY

    def commentary_is_refused(self):
        self._form_is_cleaned()
        return int(self.cleaned_data['action_option']) == self.ACTION_REFUSE

    def process_commentary(self):
        """Vet the commentary or delete it from the database"""
        if self.commentary_is_accepted():
            self.commentary.vetted = True
            self.commentary.vetted_by = Contributor.objects.get(user=self.user)
            self.commentary.save()
            return self.commentary
        elif self.commentary_is_modified() or self.commentary_is_refused():
            self.commentary.delete()
            return None


class CommentarySearchForm(forms.Form):
    """Search for Commentary specified by user"""
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False, label="Title")
    abstract = forms.CharField(max_length=1000, required=False, label="Abstract")

    def search_results(self):
        """Return all Commentary objects according to search"""
        return Commentary.objects.vetted(
            pub_title__icontains=self.cleaned_data['title'],
            pub_abstract__icontains=self.cleaned_data['abstract'],
            author_list__icontains=self.cleaned_data['author']).order_by('-pub_date')
