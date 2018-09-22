__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import os
import random
import re
import string

from datetime import datetime

from django import forms
from django.conf import settings
from django.forms import BaseFormSet, formset_factory, BaseModelFormSet, modelformset_factory
from django.template import loader
from django.utils import timezone

from ajax_select.fields import AutoCompleteSelectField

from .constants import STATUS_DRAFT, PUBLICATION_PREPUBLISHED, PUBLICATION_PUBLISHED
from .exceptions import PaperNumberingError
from .models import Issue, Publication, Reference,\
    UnregisteredAuthor, PublicationAuthorsTable, OrgPubFraction
from .utils import JournalUtils
from .signals import notify_manuscript_published


from funders.models import Grant, Funder
from journals.models import Journal
from mails.utils import DirectMailUtil
from organizations.models import Organization
from production.constants import PROOFS_PUBLISHED
from production.models import ProductionEvent
from production.signals import notify_stream_status_change
from scipost.forms import RequestFormMixin
from scipost.services import DOICaller
from submissions.constants import STATUS_PUBLISHED
from submissions.models import Submission


class UnregisteredAuthorForm(forms.ModelForm):
    class Meta:
        model = UnregisteredAuthor
        fields = ('first_name', 'last_name')


class CitationListBibitemsForm(forms.ModelForm):
    latex_bibitems = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['latex_bibitems'].widget.attrs.update(
            {'placeholder': 'Paste the .tex bibitems here'})

    def extract_dois(self):
        entries_list = self.cleaned_data['latex_bibitems']
        entries_list = re.sub(r'(?m)^\%.*\n?', '', entries_list)
        entries_list = entries_list.split('\doi{')
        dois = []
        n_entry = 1
        for entry in entries_list[1:]:  # drop first bit before first \doi{
            dois.append(
                {'key': 'ref' + str(n_entry),
                 'doi': entry.partition('}')[0], }
            )
            n_entry += 1
        return dois

    def save(self, *args, **kwargs):
        self.instance.metadata['citation_list'] = self.extract_dois()
        return super().save(*args, **kwargs)


class AbstractJATSForm(forms.ModelForm):
    abstract_jats = forms.CharField(widget=forms.Textarea({
        'placeholder': 'Paste the JATS abstract here (use pandoc to generate; see docs)'}))

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['abstract_jats'].initial = self.instance.abstract_jats

    def save(self, *args, **kwargs):
        self.instance.abstract_jats = self.cleaned_data['abstract_jats']
        return super().save(*args, **kwargs)


class FundingInfoForm(forms.ModelForm):
    funding_statement = forms.CharField(widget=forms.Textarea({
        'placeholder': 'Paste the funding info statement here'}))

    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funding_statement'].initial = self.instance.metadata.get('funding_statement')

    def save(self, *args, **kwargs):
        self.instance.metadata['funding_statement'] = self.cleaned_data['funding_statement']
        return super().save(*args, **kwargs)


class BasePublicationAuthorsTableFormSet(BaseModelFormSet):
    def save(self, *args, **kwargs):
        objects = super().save(*args, **kwargs)
        for form in self.ordered_forms:
            form.instance.order = form.cleaned_data['ORDER']
            form.instance.save()
        return objects


PublicationAuthorOrderingFormSet = modelformset_factory(
    PublicationAuthorsTable, fields=(), can_order=True, extra=0,
    formset=BasePublicationAuthorsTableFormSet)


class AuthorsTableOrganizationSelectForm(forms.ModelForm):
    organization = AutoCompleteSelectField('organization_lookup')

    class Meta:
        model = PublicationAuthorsTable
        fields = []


class CreateMetadataXMLForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['metadata_xml']

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {
            'metadata_xml': self.new_xml(kwargs.get('instance'))
        }
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.latest_metadata_update = timezone.now()
        return super().save(*args, **kwargs)

    def new_xml(self, publication):
        """
        Create new XML structure, return as a string
        """
        # Create a doi_batch_id
        salt = ""
        for i in range(5):
            salt = salt + random.choice(string.ascii_letters)
        salt = salt.encode('utf8')
        idsalt = publication.title[:10]
        idsalt = idsalt.encode('utf8')
        doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()

        funders = (Funder.objects.filter(grant__in=publication.grants.all())
                   | publication.funders_generic.all()).distinct()

        # Render from template
        template = loader.get_template('xml/publication_crossref.html')
        context = {
            'publication': publication,
            'doi_batch_id': doi_batch_id,
            'deposit_email': settings.CROSSREF_DEPOSIT_EMAIL,
            'funders': funders,
        }
        return template.render(context)


class CreateMetadataDOAJForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['metadata_DOAJ']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        kwargs['initial'] = {
            'metadata_DOAJ': self.generate(kwargs.get('instance'))
        }
        super().__init__(*args, **kwargs)

    def generate(self, publication):
        if publication.in_issue:
            issn = str(publication.in_issue.in_volume.in_journal.issn)
        else:
            issn = str(publication.in_journal.issn)
        md = {
            'bibjson': {
                'author': [{'name': publication.author_list}],
                'title': publication.title,
                'abstract': publication.abstract,
                'year': publication.publication_date.strftime('%Y'),
                'month': publication.publication_date.strftime('%m'),
                'identifier': [
                    {
                        'type': 'eissn',
                        'id': issn
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
            }
        }
        if publication.in_issue:
            md['bibjson']['journal'] = {
                'publisher': 'SciPost',
                'volume': str(publication.in_issue.in_volume.number),
                'number': str(publication.in_issue.number),
                'start_page': publication.get_paper_nr(),
                'identifier': [{
                    'type': 'eissn',
                    'id': issn
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
        else:
            md['bibjson']['journal'] = {
                'publisher': 'SciPost',
                'start_page': publication.get_paper_nr(),
                'identifier': [{
                    'type': 'eissn',
                    'id': issn
                }],
                'license': [
                    {
                        'url': self.request.build_absolute_uri(
                            publication.in_journal.get_absolute_url()),
                        'open_access': 'true',
                        'type': publication.get_cc_license_display(),
                        'title': publication.get_cc_license_display(),
                    }
                ],
                'language': ['EN'],
                'title': publication.in_journal.get_name_display(),
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

    def __init__(self, data=None, identifier_w_vn_nr=None, issue_id=None, *args, **kwargs):
        # Use separate instance to be able to prefill the form without any existing Publication
        self.submission = None
        self.issue = None
        self.to_journal = None
        if identifier_w_vn_nr:
            try:
                self.submission = Submission.objects.accepted().get(
                    preprint__identifier_w_vn_nr=identifier_w_vn_nr)
            except Submission.DoesNotExist:
                self.submission = None

        # Check if the Submission is related to a Journal with individual Publications only
        if self.submission:
            try:
                self.to_journal = Journal.objects.has_individual_publications().get(
                    name=self.submission.submitted_to_journal)
            except Journal.DoesNotExist:
                self.to_journal = None

        # If the Journal is not for individual publications, choose a Issue for Publication
        if issue_id and not self.to_journal:
            try:
                self.issue = self.get_possible_issues().get(id=issue_id)
            except Issue.DoesNotExist:
                self.issue = None

        super().__init__(data, *args, **kwargs)

        if kwargs.get('instance') or self.issue or self.to_journal:
            # When updating: fix in_issue, because many fields are directly related to the issue.
            del self.fields['in_issue']
            self.prefill_fields()
        else:
            self.fields['in_issue'].queryset = self.get_possible_issues()
            self.delete_secondary_fields()

    def get_possible_issues(self):
        issues = Issue.objects.filter(until_date__gte=timezone.now())
        if self.submission:
            issues = issues.for_journal(self.submission.submitted_to_journal)
        return issues

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

    def clean(self):
        data = super().clean()
        if not self.instance.id:
            if self.submission:
                self.instance.accepted_submission = self.submission
            if self.issue:
                self.instance.in_issue = self.issue
            if self.to_journal:
                self.instance.in_journal = self.to_journal
        return data

    def save(self, *args, **kwargs):
        """
        Save the Publication object always as a draft and prefill the Publication with
        related Submission data only when appending the Publication.
        """
        do_prefill = False
        if not self.instance.id:
            do_prefill = True
        super().save(*args, **kwargs)
        if do_prefill:
            self.first_time_fill()
        return self.instance

    def first_time_fill(self):
        """
        Take over fields from related Submission object. This can only be done after
        the Publication object has been added to the database due to m2m relations.
        """
        self.instance.status = STATUS_DRAFT

        if self.submission:
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
            self.fields['publication_date'].initial = timezone.now()

        # Fill data that may be derived from the issue data
        issue = None
        if hasattr(self.instance, 'in_issue') and self.instance.in_issue:
            issue = self.instance.in_issue
        elif self.issue:
            issue = self.issue
        if issue:
            self.prefill_with_issue(issue)

        # Fill data that may be derived from the issue data
        journal = None
        if hasattr(self.instance, 'in_journal') and self.instance.in_journal:
            journal = self.instance.in_issue
        elif self.to_journal:
            journal = self.to_journal
        if journal:
            self.prefill_with_journal(journal)

    def prefill_with_issue(self, issue):
        # Determine next available paper number:
        paper_nr = Publication.objects.filter(in_issue__in_volume=issue.in_volume).count() + 1
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
            issue.in_volume.in_journal.abbreviation_citation,
            issue.in_volume.number,
            issue.number,
            paper_nr,
            issue.until_date.strftime('%Y'),
            doi_string,
            doi_string)
        self.fields['BiBTeX_entry'].initial = bibtex_entry
        if not self.instance.BiBTeX_entry:
            self.instance.BiBTeX_entry = bibtex_entry

    def prefill_with_journal(self, journal):
        # Determine next available paper number:
        paper_nr = journal.publications.count() + 1
        self.fields['paper_nr'].initial = str(paper_nr)
        doi_label = '{journal}.{paper}'.format(
            journal=journal.name,
            paper=paper_nr)
        self.fields['doi_label'].initial = doi_label

        doi_string = '10.21468/{doi}'.format(doi=doi_label)
        bibtex_entry = (
            '@Article{%s,\n'
            '\ttitle={{%s},\n'
            '\tauthor={%s},\n'
            '\tjournal={%s},\n'
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
            journal.abbreviation_citation,
            paper_nr,
            timezone.now().year,
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


class PublicationPublishForm(RequestFormMixin, forms.ModelForm):
    class Meta:
        model = Publication
        fields = []

    def move_pdf(self):
        """
        To keep the Publication pdfs organized we move the pdfs to their own folder
        organized by journal and optional issue folder.
        """
        initial_path = self.instance.pdf_file.path

        new_dir = ''
        if self.instance.in_issue:
            new_dir += self.instance.in_issue.path
        elif self.instance.in_journal:
            new_dir += 'SCIPOST_JOURNALS/{name}'.format(name=self.instance.in_journal.name)

        new_dir += '/{paper_nr}'.format(paper_nr=self.instance.get_paper_nr())
        os.makedirs(settings.MEDIA_ROOT + new_dir, exist_ok=True)

        new_dir += '/{doi}.pdf'.format(doi=self.instance.doi_label.replace('.', '_'))
        os.rename(initial_path, settings.MEDIA_ROOT + new_dir)
        self.instance.pdf_file.name = new_dir
        self.instance.status = PUBLICATION_PUBLISHED
        self.instance.save()

    def update_submission(self):
        # Mark the submission as having been published:
        submission = self.instance.accepted_submission
        submission.published_as = self.instance
        submission.status = STATUS_PUBLISHED
        submission.save()

        # Add SubmissionEvents
        submission.add_general_event(
            'The Submission has been published as %s.' % self.instance.doi_label)

    def update_stream(self):
        # Update ProductionStream
        submission = self.instance.accepted_submission
        if hasattr(submission, 'production_stream'):
            stream = submission.production_stream
            stream.status = PROOFS_PUBLISHED
            stream.save()
            if self.request.user.production_user:
                prodevent = ProductionEvent(
                    stream=stream,
                    event='status',
                    comments=' published the manuscript.',
                    noted_by=self.request.user.production_user
                )
                prodevent.save()
            notify_stream_status_change(self.request.user, stream, False)

    def save(self, commit=True):
        if commit:
            self.move_pdf()
            self.update_submission()
            self.update_stream()

            # Email authors
            JournalUtils.load({'publication': self.instance})
            JournalUtils.send_authors_paper_published_email()
            notify_manuscript_published(self.request.user, self.instance, False)

        return self.instance



class SetOrgPubFractionForm(forms.ModelForm):
    class Meta:
        model = OrgPubFraction
        fields = ['organization', 'publication', 'fraction']

    def __init__(self, *args, **kwargs):
        super(SetOrgPubFractionForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['organization'].disabled = True
            self.fields['publication'].widget = forms.HiddenInput()


class BaseOrgPubFractionsFormSet(BaseModelFormSet):

    def clean(self):
        """
        Checks that the fractions add up to one.
        """
        cleaned_data = super().clean()
        norm = 0
        for form in self.forms:
            norm += 1000 * form.cleaned_data['fraction']
        if norm != 1000:
            raise forms.ValidationError('The fractions do not add up to one!')


OrgPubFractionsFormSet = modelformset_factory(OrgPubFraction,
                                              fields=('publication', 'organization', 'fraction'),
                                              formset=BaseOrgPubFractionsFormSet,
                                              form=SetOrgPubFractionForm, extra=0)
