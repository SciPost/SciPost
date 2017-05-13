import re

from django import forms
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Commentary

from scipost.services import DOICaller, ArxivCaller
from scipost.models import Contributor


def commentary_exists(input_doi):
    return Commentary.objects.filter(pub_DOI=input_doi).exists()


class DOIToQueryForm(forms.Form):
    VALID_DOI_REGEXP = r'^(?i)10.\d{4,9}/[-._;()/:A-Z0-9]+$'
    doi = forms.RegexField(regex=VALID_DOI_REGEXP, strip=False, widget=forms.TextInput(
        {'label': 'DOI', 'placeholder': 'ex.: 10.21468/00.000.000000'}))

    def clean_doi(self):
        input_doi = self.cleaned_data['doi']

        if commentary_exists(input_doi):
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

    identifier = forms.RegexField(regex=VALID_ARXIV_IDENTIFIER_REGEX, strip=True)

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


# class IdentifierToQueryForm(forms.Form):
#     identifier = forms.CharField(widget=forms.TextInput(
#         {'label': 'arXiv identifier',
#          'placeholder': 'new style ####.####(#)v# or old-style e.g. cond-mat/#######'}))
#
#     def clean(self, *args, **kwargs):
#         cleaned_data = super(IdentifierToQueryForm, self).clean(*args, **kwargs)
#
#         identifierpattern_new = re.compile("^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$")
#         identifierpattern_old = re.compile("^[-.a-z]+/[0-9]{7,}v[0-9]{1,2}$")
#
#         if not (identifierpattern_new.match(cleaned_data['identifier']) or
#                 identifierpattern_old.match(cleaned_data['identifier'])):
#                 msg = ('The identifier you entered is improperly formatted '
#                        '(did you forget the version number?)')
#                 self.add_error('identifier', msg)
#
#         try:
#             commentary = Commentary.objects.get(arxiv_identifier=cleaned_data['identifier'])
#         except (Commentary.DoesNotExist, KeyError):
#             # Commentary either does not exists or form is invalid
#             commentary = None
#
#         if commentary:
#             msg = 'There already exists a Commentary Page on this preprint, see %s' % (
#                     commentary.title_label())
#             self.add_error('identifier', msg)
#         return cleaned_data

class RequestCommentaryForm(forms.ModelForm):
    class Meta:
        model = Commentary
        fields = [
            'discipline', 'domain', 'subject_area', 'pub_title', 'author_list', 'pub_date', 'pub_DOI', 'pub_abstract'
        ]
        placeholders = {
            'pub_date': 'Format: YYYY-MM-DD'
        }


class RequestArxivPreprintForm(RequestCommentaryForm):
    class Meta(RequestCommentaryForm.Meta):
        model = Commentary
        fields = RequestCommentaryForm.Meta.fields + ['arxiv_identifier']


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

        if commentary_exists(input_doi):
            error_message = 'There already exists a Commentary Page on this publication.'
            raise forms.ValidationError(error_message)

        return input_doi


# class RequestCommentaryForm(forms.ModelForm):
#     """Create new valid Commetary by user request"""
#     existing_commentary = None
#
#     class Meta:
#         model = Commentary
#         fields = ['type', 'discipline', 'domain', 'subject_area',
#                   'pub_title', 'author_list',
#                   'metadata',
#                   'journal', 'volume', 'pages', 'pub_date',
#                   'arxiv_identifier',
#                   'pub_DOI', 'pub_abstract']
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super(RequestCommentaryForm, self).__init__(*args, **kwargs)
#         self.fields['metadata'].widget = forms.HiddenInput()
#         self.fields['pub_date'].widget.attrs.update({'placeholder': 'Format: YYYY-MM-DD'})
#         self.fields['arxiv_identifier'].widget.attrs.update(
#             {'placeholder': 'ex.:  1234.56789v1 or cond-mat/1234567v1'})
#         self.fields['pub_DOI'].widget.attrs.update({'placeholder': 'ex.: 10.21468/00.000.000000'})
#         self.fields['pub_abstract'].widget.attrs.update({'cols': 100})
#
#     def clean(self, *args, **kwargs):
#         """Check if form is valid and contains an unique identifier"""
#         cleaned_data = super(RequestCommentaryForm, self).clean(*args, **kwargs)
#
#         # Either Arxiv-ID or DOI is given
#         if not cleaned_data['arxiv_identifier'] and not cleaned_data['pub_DOI']:
#             msg = ('You must provide either a DOI (for a published paper) '
#                    'or an arXiv identifier (for a preprint).')
#             self.add_error('arxiv_identifier', msg)
#             self.add_error('pub_DOI', msg)
#         elif (cleaned_data['arxiv_identifier'] and
#               (Commentary.objects
#                .filter(arxiv_identifier=cleaned_data['arxiv_identifier']).exists())):
#             msg = 'There already exists a Commentary Page on this preprint, see'
#             self.existing_commentary = get_object_or_404(
#                 Commentary,
#                 arxiv_identifier=cleaned_data['arxiv_identifier'])
#             self.add_error('arxiv_identifier', msg)
#         elif (cleaned_data['pub_DOI'] and
#               Commentary.objects.filter(pub_DOI=cleaned_data['pub_DOI']).exists()):
#             msg = 'There already exists a Commentary Page on this publication, see'
#             self.existing_commentary = get_object_or_404(
#                 Commentary, pub_DOI=cleaned_data['pub_DOI'])
#             self.add_error('pub_DOI', msg)
#
#         # Current user is not known
#         if not self.user or not Contributor.objects.filter(user=self.user).exists():
#             self.add_error(None, 'Sorry, current user is not known to SciPost.')
#
#     def save(self, *args, **kwargs):
#         """Prefill instance before save"""
#         self.instance.requested_by = Contributor.objects.get(user=self.user)
#         return super(RequestCommentaryForm, self).save(*args, **kwargs)
#
#     def get_existing_commentary(self):
#         """Get Commentary if found after validation"""
#         return self.existing_commentary


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
