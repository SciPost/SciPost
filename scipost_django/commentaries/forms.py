__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import get_template

from .models import Commentary
from .constants import COMMENTARY_PUBLISHED, COMMENTARY_PREPRINT

from comments.forms import CommentForm
from scipost.services import DOICaller, ArxivCaller

import strings


class DOIToQueryForm(forms.Form):
    VALID_DOI_REGEXP = r'(?i)10.\d{4,9}/[-._;()/:A-Z0-9]+$'
    doi = forms.RegexField(
        regex=VALID_DOI_REGEXP, strip=True, help_text=strings.doi_query_help_text,
        error_messages={'invalid': strings.doi_query_invalid},
        widget=forms.TextInput({'label': 'DOI','placeholder': strings.doi_query_placeholder}))

    def clean_doi(self):
        input_doi = self.cleaned_data['doi']

        commentary = Commentary.objects.filter(pub_DOI=input_doi)
        if commentary.exists():
            error_message = get_template('commentaries/_doi_query_commentary_exists.html').render(
                {'arxiv_or_DOI_string': commentary[0].arxiv_or_DOI_string}
            )
            raise forms.ValidationError(mark_safe(error_message))

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

    identifier = forms.RegexField(regex=VALID_ARXIV_IDENTIFIER_REGEX,
                                  strip=True,
                                  help_text=strings.arxiv_query_help_text,
                                  error_messages={'invalid': strings.arxiv_query_invalid},
                                  widget=forms.TextInput({
                                        'placeholder': strings.arxiv_query_placeholder}))

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']

        commentary = Commentary.objects.filter(arxiv_identifier=identifier)
        if commentary.exists():
            error_message = get_template('commentaries/_doi_query_commentary_exists.html').render(
                {'arxiv_or_DOI_string': commentary[0].arxiv_or_DOI_string}
            )
            raise forms.ValidationError(mark_safe(error_message))

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
            'acad_field', 'specialties', 'approaches', 'title',
            'author_list', 'pub_date', 'pub_abstract'
        ]
        placeholders = {
            'pub_date': 'Format: YYYY-MM-DD'
        }

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by', None)
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.parse_links_into_urls(commit=False)
        if self.requested_by:
            self.instance.requested_by = self.requested_by
        return super().save(*args, **kwargs)


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

        commentary = Commentary.objects.filter(arxiv_identifier=arxiv_identifier)
        if commentary.exists():
            error_message = get_template('commentaries/_doi_query_commentary_exists.html').render(
                {'arxiv_or_DOI_string': commentary[0].arxiv_or_DOI_string}
            )
            raise forms.ValidationError(mark_safe(error_message))

        return arxiv_identifier

    def save(self, *args, **kwargs):
        self.instance.type = COMMENTARY_PREPRINT
        return super().save(*args, **kwargs)


class RequestPublishedArticleForm(RequestCommentaryForm):
    class Meta(RequestCommentaryForm.Meta):
        fields = RequestCommentaryForm.Meta.fields + ['journal', 'volume', 'pages', 'pub_DOI']
        placeholders = {
            **RequestCommentaryForm.Meta.placeholders,
            **{'pub_DOI': 'ex.: 10.21468/00.000.000000'}
        }

    def __init__(self, *args, **kwargs):
        super(RequestPublishedArticleForm, self).__init__(*args, **kwargs)
        # We want pub_DOI to be a required field.
        # Since it can be blank on the model, we have to override this property here.
        self.fields['pub_DOI'].required = True

    def clean_pub_DOI(self):
        input_doi = self.cleaned_data['pub_DOI']

        commentary = Commentary.objects.filter(pub_DOI=input_doi)
        if commentary.exists():
            error_message = get_template('commentaries/_doi_query_commentary_exists.html').render(
                {'arxiv_or_DOI_string': commentary[0].arxiv_or_DOI_string}
            )
            raise forms.ValidationError(mark_safe(error_message))

        return input_doi

    def save(self, *args, **kwargs):
        self.instance.type = COMMENTARY_PUBLISHED
        return super().save(*args, **kwargs)


class VetCommentaryForm(forms.Form):
    """Process an unvetted Commentary request.

    This form will provide fields to let the user
    process a Commentary that is unvetted. On success,
    the Commentary is either accepted or deleted from
    the database.

    Keyword arguments:

    * commentary_id -- the Commentary.id to process (required)
    * user -- User instance of the vetting user (required)

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

    def clean_refusal_reason(self):
        """`refusal_reason` field is required if action==refuse."""
        if self.commentary_is_refused():
            if int(self.cleaned_data['refusal_reason']) == self.REFUSAL_EMPTY:
                self.add_error('refusal_reason', 'Please, choose a reason for rejection.')
        return self.cleaned_data['refusal_reason']

    def get_commentary(self):
        """Return Commentary if available"""
        self._form_is_cleaned()
        return self.commentary

    def get_refusal_reason(self):
        """Return refusal reason"""
        if self.commentary_is_refused():
            return self.COMMENTARY_REFUSAL_DICT[int(self.cleaned_data['refusal_reason'])]

    def commentary_is_accepted(self):
        return int(self.cleaned_data['action_option']) == self.ACTION_ACCEPT

    def commentary_is_modified(self):
        return int(self.cleaned_data['action_option']) == self.ACTION_MODIFY

    def commentary_is_refused(self):
        return int(self.cleaned_data['action_option']) == self.ACTION_REFUSE

    def process_commentary(self):
        """Vet the commentary or delete it from the database"""
        # Modified actions are not doing anything. Users are redirected to an edit page instead.
        if self.commentary_is_accepted():
            self.commentary.vetted = True
            self.commentary.vetted_by = self.user.contributor
            self.commentary.save()
            return self.commentary
        elif self.commentary_is_refused():
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
            title__icontains=self.cleaned_data['title'],
            pub_abstract__icontains=self.cleaned_data['abstract'],
            author_list__icontains=self.cleaned_data['author']).order_by('-pub_date')


class CommentSciPostPublication(CommentForm):
    """
    This Form will let authors of a SciPost publication comment on their Publication
    using the Commentary functionalities. It will create a Commentary page if it does not
    exist yet.

    It inherits from ModelForm: CommentForm and thus will, by default, return a Comment!
    """

    def __init__(self, *args, **kwargs):
        self.publication = kwargs.pop('publication')
        self.current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Create (vetted) Commentary page if not exist and do save actions as
        per original CommentForm.
        """
        if not commit:
            raise AssertionError('CommentSciPostPublication can only be used with commit=True')

        try:
            commentary = self.publication.commentary
        except Commentary.DoesNotExist:
            submission = self.publication.accepted_submission
            commentary = Commentary(**{
                # 'vetted_by': None,
                'requested_by': self.current_user.contributor,
                'vetted': True,
                'type': COMMENTARY_PUBLISHED,
                'acad_field': self.publication.acad_field,
                'specialties': self.publication.specialties,
                'approaches': self.publication.approaches,
                'title': self.publication.title,
                'arxiv_identifier': submission.preprint.identifier_w_vn_nr,
                'arxiv_link': submission.preprint.url,
                'pub_DOI': self.publication.doi_string,
                'metadata': self.publication.metadata,
                'scipost_publication': self.publication,
                'author_list': self.publication.author_list,
                'journal': self.publication.in_issue.in_volume.in_journal.name,
                'pages': self.publication.in_issue.number,
                'volume': self.publication.in_issue.in_volume.number,
                'pub_date': self.publication.publication_date,
                'pub_abstract': self.publication.abstract,
            })
            commentary.parse_links_into_urls(commit=False)
            commentary.save()
            commentary.authors.add(*self.publication.authors.all())

        # Original saving steps
        comment = super().save(commit=False)
        comment.author = self.current_user.contributor
        comment.is_author_reply = True
        comment.content_object = commentary
        comment.save()
        comment.grant_permissions()
        return comment
