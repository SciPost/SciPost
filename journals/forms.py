import re

from datetime import datetime

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from django.utils import timezone

from .models import Issue, Publication, Reference, UnregisteredAuthor

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
        exclude = ['authors', 'authors_claims', 'authors_false_claims',
                   'metadata', 'metadata_xml',
                   'latest_activity']


class UnregisteredAuthorForm(forms.ModelForm):
    class Meta:
        model = UnregisteredAuthor
        fields = ('first_name', 'last_name')


class CitationListBibitemsForm(forms.Form):
    latex_bibitems = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(CitationListBibitemsForm, self).__init__(*args, **kwargs)
        self.fields['latex_bibitems'].widget.attrs.update(
            {'rows': 30, 'cols': 50, 'placeholder': 'Paste the .tex bibitems here'})

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


class FundingInfoForm(forms.Form):
    funding_statement = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funding_statement'].widget.attrs.update({
            'rows': 10,
            'cols': 50,
            'placeholder': 'Paste the funding info statement here'
        })


class CreateMetadataXMLForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['metadata_xml']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metadata_xml'].widget.attrs.update({
            'rows': 50,
            'cols': 50
        })


class CreateMetadataDOAJForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.metadata_DOAJ = self.generate(self.instance)
        super().save(*args, **kwargs)

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
