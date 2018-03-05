import re

from datetime import datetime

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from django.utils import timezone

from .constants import STATUS_DRAFT, PUBLICATION_PREPUBLISHED
from .exceptions import PaperNumberingError
from .models import Issue, Publication, Reference, UnregisteredAuthor, PublicationAuthorsTable

from funders.models import Grant
from mails.utils import DirectMailUtil
from scipost.services import DOICaller
from submissions.models import Submission


class InitiatePublicationForm(forms.Form):
    accepted_submission = forms.ModelChoiceField(queryset=Submission.objects.accepted())
    to_be_issued_in = forms.ModelChoiceField(
        queryset=Issue.objects.filter(until_date__gte=timezone.now()))

    def __init__(self, *args, **kwargs):
        super(InitiatePublicationForm, self).__init__(*args, **kwargs)


class ValidatePublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        exclude = ['authors_claims', 'authors_false_claims',
                   'metadata', 'metadata_xml', 'authors_registered',
                   'authors_unregistered', 'latest_activity']


class UnregisteredAuthorForm(forms.ModelForm):
    class Meta:
        model = UnregisteredAuthor
        fields = ('first_name', 'last_name')


class CitationListBibitemsForm(forms.Form):
    latex_bibitems = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['latex_bibitems'].widget.attrs.update(
            {'placeholder': 'Paste the .tex bibitems here'})

    def extract_dois(self):
        entries_list = self.cleaned_data['latex_bibitems']
        entries_list = re.sub(r'(?m)^\%.*\n?', '', entries_list)
        entries_list = entries_list.split('\doi{')
        dois = []
        nentries = 1
        for entry in entries_list[1:]:  # drop first bit before first \doi{
            dois.append(
                {'key': 'ref' + str(nentries),
                 'doi': entry.partition('}')[0], }
            )
            nentries += 1
        return dois


class FundingInfoForm(forms.ModelForm):
    funding_statement = forms.CharField(widget=forms.Textarea({
        'placeholder': 'Paste the funding info statement here'}))

    class Meta:
        model = Publication
        fields = ()

    def save(self, *args, **kwargs):
        self.instance.metadata['funding_statement'] = self.cleaned_data['funding_statement']
        return super().save(*args, **kwargs)


class CreateMetadataXMLForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['metadata_xml']


class CreateMetadataDOAJForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.metadata_DOAJ = self.generate(self.instance)
        return super().save(*args, **kwargs)

    def generate(self, publication):
        md = {
            'bibjson': {
                'author': [{'name': publication.author_list}],
                'title': publication.title,
                'abstract': publication.abstract,
                'year': publication.publication_date.strftime('%Y'),
                'month': publication.publication_date.strftime('%m'),
                'start_page': publication.get_paper_nr(),
                'identifier': [
                    {
                        'type': 'eissn',
                        'id': str(publication.in_issue.in_volume.in_journal.issn)
                    },
                    {
                        'type': 'doi',
                        'id': publication.doi_string
                    }
                ],
                'link': [
                    {
                        'url': self.request.build_absolute_uri(publication.get_absolute_url()),
                        'type': 'fulltext',
                    }
                ],
                'journal': {
                    'publisher': 'SciPost',
                    'volume': str(publication.in_issue.in_volume.number),
                    'number': str(publication.in_issue.number),
                    'identifier': [{
                        'type': 'eissn',
                        'id': str(publication.in_issue.in_volume.in_journal.issn)
                    }],
                    'license': [
                        {
                            'url': self.request.build_absolute_uri(
                                publication.in_issue.in_volume.in_journal.get_absolute_url()),
                            'open_access': 'true',
                            'type': publication.get_cc_license_display(),
                            'title': publication.get_cc_license_display(),
                        }
                    ],
                    'language': ['EN'],
                    'title': publication.in_issue.in_volume.in_journal.get_name_display(),
                }
            }
        }
        return md


class BaseReferenceFormSet(BaseModelFormSet):
    """
    BaseReferenceFormSet is used to help fill the Reference list for Publications

    It is required to add the required keyword argument `publication` to this FormSet.
    """
    initial_references = []

    def __init__(self, *args, **kwargs):
        self.publication = kwargs.pop('publication')
        extra = kwargs.pop('extra')
        self.extra = int(extra if extra else '0')
        kwargs['form_kwargs'] = {'publication': self.publication}
        super().__init__(*args, **kwargs)

    def prefill(self):
        citations = self.publication.metadata.get('citation_list', [])

        for cite in citations:
            caller = DOICaller(cite['doi'])

            if caller.is_valid:
                # Authors
                author_list = []
                for author in caller._crossref_data['author'][:3]:
                    try:
                        author_list.append('{}. {}'.format(author['given'][0], author['family']))
                    except KeyError:
                        author_list.append(author['name'])

                if len(author_list) > 2:
                    authors = ', '.join(author_list[:-1])
                    authors += ' and ' + author_list[-1]
                else:
                    authors = ' and '.join(author_list)

                # Citation
                citation = '<em>{}</em> {} <b>{}</b>, {} ({})'.format(
                    caller.data['title'],
                    caller.data['journal'],
                    caller.data['volume'],
                    caller.data['pages'],
                    datetime.strptime(caller.data['pub_date'], '%Y-%m-%d').year)

                self.initial_references.append({
                    'reference_number': cite['key'][3:],
                    'authors': authors,
                    'citation': citation,
                    'identifier': cite['doi'],
                    'link': 'https://doi.org/{}'.format(cite['doi']),
                })
            else:
                self.initial_references.append({
                    'reference_number': cite['key'][3:],
                    'identifier': cite['doi'],
                    'link': 'https://doi.org/{}'.format(cite['doi']),
                })

        # Add prefill information to the form
        if not self.initial_extra:
            self.initial_extra = self.initial_references
        else:
            self.initial_extra.extend(self.initial_references)
        self.extra += len(self.initial_extra)


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            'reference_number',
            'authors',
            'citation',
            'identifier',
            'link',
        ]

    def __init__(self, *args, **kwargs):
        self.publication = kwargs.pop('publication')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.publication = self.publication
        super().save(*args, **kwargs)


ReferenceFormSet = modelformset_factory(Reference, formset=BaseReferenceFormSet,
                                        form=ReferenceForm, can_delete=True)


class DraftPublicationForm(forms.ModelForm):
    """
    This Form is used by the Production Supervisors to create a new Publication object
    and prefill all data. It is only able to create a `draft` version of a Publication object.
    """
    class Meta:
        model = Publication
        fields = [
            'doi_label',
            'pdf_file',
            'in_issue',
            'paper_nr',
            'title',
            'author_list',
            'abstract',
            'discipline',
            'domain',
            'subject_area',
            'secondary_areas',
            'cc_license',
            'BiBTeX_entry',
            'submission_date',
            'acceptance_date',
            'publication_date']

    def __init__(self, data=None, arxiv_identifier_w_vn_nr=None, issue_id=None, *args, **kwargs):
        # Use separate instance to be able to prefill the form without any existing Publication
        self.submission = None
        self.issue = None
        if arxiv_identifier_w_vn_nr:
            self.submission = Submission.objects.accepted().get(
                arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
        if issue_id:
            self.issue = Issue.objects.filter(until_date__gte=timezone.now()).get(id=issue_id)
        super().__init__(data, *args, **kwargs)
        if kwargs.get('instance') or self.issue:
            # When updating: fix in_issue, because many fields are directly related to the issue.
            del self.fields['in_issue']
            self.prefill_fields()
        else:
            self.fields['in_issue'].queryset = Issue.objects.filter(until_date__gte=timezone.now())
            self.delete_secondary_fields()


    def delete_secondary_fields(self):
        """
        Delete fields from the self.fields dictionary. Later on, this submitted sparse form can
        be used to prefill these secondary fields.
        """
        del self.fields['doi_label']
        del self.fields['pdf_file']
        del self.fields['paper_nr']
        del self.fields['title']
        del self.fields['author_list']
        del self.fields['abstract']
        del self.fields['discipline']
        del self.fields['domain']
        del self.fields['subject_area']
        del self.fields['secondary_areas']
        del self.fields['cc_license']
        del self.fields['BiBTeX_entry']
        del self.fields['submission_date']
        del self.fields['acceptance_date']
        del self.fields['publication_date']

    def save(self, *args, **kwargs):
        """
        Save the Publication object always as a draft and prefill the Publication with
        related Submission data only when appending the Publication.
        """
        self.instance.status = STATUS_DRAFT
        do_prefill = False
        if not self.instance.id:
            do_prefill = True
            self.instance.accepted_submission = self.submission
            self.instance.in_issue = self.issue
        self.instance = super().save(*args, **kwargs)
        if do_prefill:
            self.first_time_fill()
        return self.instance

    def first_time_fill(self):
        """
        Take over fields from related Submission object. This can only be done after
        the Publication object has been added to the database due to m2m relations.
        """
        # Copy all existing author and non-author relations to Publication
        for submission_author in self.submission.authors.all():
            PublicationAuthorsTable.objects.create(
                publication=self.instance, contributor=submission_author)
        self.instance.authors_claims.add(*self.submission.authors_claims.all())
        self.instance.authors_false_claims.add(*self.submission.authors_false_claims.all())

        # Add Institutions to the publication related to the current authors
        for author in self.instance.authors_registered.all():
            for current_affiliation in author.affiliations.active():
                self.instance.institutions.add(current_affiliation.institution)

    def prefill_fields(self):
        if self.submission:
            self.fields['title'].initial = self.submission.title
            self.fields['author_list'].initial = self.submission.author_list
            self.fields['abstract'].initial = self.submission.abstract
            self.fields['discipline'].initial = self.submission.discipline
            self.fields['domain'].initial = self.submission.domain
            self.fields['subject_area'].initial = self.submission.subject_area
            self.fields['secondary_areas'].initial = self.submission.secondary_areas
            self.fields['submission_date'].initial = self.submission.submission_date
            self.fields['acceptance_date'].initial = self.submission.acceptance_date

        # Fill data that may be derived from the issue data
        issue = self.instance.in_issue if hasattr(self.instance, 'in_issue') else self.issue
        if issue:
            # Determine next available paper number:
            paper_nr = Publication.objects.filter(in_issue__in_volume=issue.in_volume).count()
            paper_nr += paper_nr
            if paper_nr > 999:
                raise PaperNumberingError(paper_nr)
            self.fields['paper_nr'].initial = str(paper_nr)
            doi_label = '{journal}.{vol}.{issue}.{paper}'.format(
                journal=issue.in_volume.in_journal.name,
                vol=issue.in_volume.number,
                issue=issue.number,
                paper=str(paper_nr).rjust(3, '0'))
            self.fields['doi_label'].initial = doi_label

            doi_string = '10.21468/{doi}'.format(doi=doi_label)
            bibtex_entry = (
                '@Article{%s,\n'
                '\ttitle={{%s},\n'
                '\tauthor={%s},\n'
                '\tjournal={%s},\n'
                '\tvolume={%i},\n'
                '\tissue={%i},\n'
                '\tpages={%i},\n'
                '\tyear={%s},\n'
                '\tpublisher={SciPost},\n'
                '\tdoi={%s},\n'
                '\turl={https://scipost.org/%s},\n'
                '}'
            ) % (
                doi_string,
                self.submission.title,
                self.submission.author_list.replace(',', ' and'),
                issue.in_volume.in_journal.get_abbreviation_citation(),
                issue.in_volume.number,
                issue.number,
                paper_nr,
                issue.until_date.strftime('%Y'),
                doi_string,
                doi_string)
            self.fields['BiBTeX_entry'].initial = bibtex_entry
            if not self.instance.BiBTeX_entry:
                self.instance.BiBTeX_entry = bibtex_entry


class DraftPublicationApprovalForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ()

    def save(self, commit=True):
        self.instance.status = PUBLICATION_PREPUBLISHED
        if commit:
            self.instance.save()
            mail_sender = DirectMailUtil(mail_code='publication_ready', instance=self.instance)
            mail_sender.send()
        return self.instance


class PublicationGrantsForm(forms.ModelForm):
    grant = forms.ModelChoiceField(queryset=Grant.objects.none())

    class Meta:
        model = Publication
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grant'].queryset = Grant.objects.exclude(
            id__in=self.instance.grants.values_list('id', flat=True))

    def save(self, commit=True):
        if commit:
            self.instance.grants.add(self.cleaned_data['grant'])
        return self.instance
