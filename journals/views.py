import hashlib
import json
import os
import random
import requests
import shutil
import string
import xml.etree.ElementTree as ET


from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404, render, redirect

from .constants import STATUS_DRAFT
from .helpers import paper_nr_string, issue_doi_label_from_doi_label
from .models import Journal, Issue, Publication, Deposit, DOAJDeposit,\
                    GenericDOIDeposit, PublicationAuthorsTable
from .forms import FundingInfoForm,\
                   UnregisteredAuthorForm, CreateMetadataXMLForm, CitationListBibitemsForm,\
                   ReferenceFormSet, CreateMetadataDOAJForm, DraftPublicationForm,\
                   PublicationGrantsForm, DraftPublicationApprovalForm, PublicationPublishForm
from .mixins import PublicationMixin, ProdSupervisorPublicationPermissionMixin
from .utils import JournalUtils

from comments.models import Comment
from funders.forms import FunderSelectForm, GrantSelectForm
from funders.models import Funder, Grant
from submissions.models import Submission, Report
from scipost.forms import ConfirmationForm
from scipost.models import Contributor
from scipost.mixins import PermissionsMixin, RequestViewMixin

from guardian.decorators import permission_required


############
# Journals
############

def journals(request):
    '''Main landing page for Journals application.'''
    context = {'journals': Journal.objects.order_by('name')}
    return render(request, 'journals/journals.html', context)


def landing_page(request, doi_label):
    journal = get_object_or_404(Journal, doi_label=doi_label)

    current_issue = Issue.objects.published(
        in_volume__in_journal=journal,
        start_date__lte=timezone.now(),
        until_date__gte=timezone.now()).order_by('-until_date').first()
    latest_issue = Issue.objects.published(
        in_volume__in_journal=journal,
        until_date__lte=timezone.now()).order_by('-until_date').first()

    prev_issue = None
    if current_issue:
        prev_issue = (Issue.objects.published(in_volume__in_journal=journal,
                                              start_date__lt=current_issue.start_date)
                                   .order_by('start_date').last())

    context = {
        'current_issue': current_issue,
        'latest_issue': latest_issue,
        'prev_issue': prev_issue,
        'journal': journal
    }
    return render(request, 'journals/journal_landing_page.html', context)


def issues(request, doi_label):
    journal = get_object_or_404(Journal, doi_label=doi_label)

    issues = Issue.objects.published(in_volume__in_journal=journal).order_by('-until_date')
    context = {
        'issues': issues,
        'journal': journal
    }
    return render(request, 'journals/journal_issues.html', context)


def recent(request, doi_label):
    """
    Display page for the most recent 20 publications in SciPost Physics.
    """
    journal = get_object_or_404(Journal, doi_label=doi_label)
    recent_papers = Publication.objects.published().filter(
        in_issue__in_volume__in_journal=journal).order_by('-publication_date',
                                                          '-paper_nr')[:20]
    context = {
        'recent_papers': recent_papers,
        'journal': journal,
    }
    return render(request, 'journals/journal_recent.html', context)


def accepted(request, doi_label):
    """
    Display page for submissions to SciPost Physics which
    have been accepted but are not yet published.
    """
    journal = get_object_or_404(Journal, doi_label=doi_label)
    accepted_SP_submissions = (Submission.objects.accepted()
                               .filter(submitted_to_journal=journal.name)
                               .order_by('-latest_activity'))
    context = {
        'accepted_SP_submissions': accepted_SP_submissions,
        'journal': journal
    }
    return render(request, 'journals/journal_accepted.html', context)


def info_for_authors(request, doi_label):
    journal = get_object_or_404(Journal, doi_label=doi_label)
    context = {
        'journal': journal
    }
    return render(request, 'journals/%s_info_for_authors.html' % doi_label, context)


def about(request, doi_label):
    journal = get_object_or_404(Journal, doi_label=doi_label)
    context = {
        'journal': journal
    }
    return render(request, 'journals/%s_about.html' % doi_label, context)


def issue_detail(request, doi_label):
    issue = Issue.objects.get_published(doi_label=doi_label)
    journal = issue.in_volume.in_journal

    papers = issue.publications.published().order_by('paper_nr')
    next_issue = (Issue.objects.published(in_volume__in_journal=journal,
                                          start_date__gt=issue.start_date)
                               .order_by('start_date').first())
    prev_issue = (Issue.objects.published(in_volume__in_journal=journal,
                                          start_date__lt=issue.start_date)
                               .order_by('start_date').last())
    context = {
        'issue': issue,
        'prev_issue': prev_issue,
        'next_issue': next_issue,
        'papers': papers,
        'journal': journal
    }
    return render(request, 'journals/journal_issue_detail.html', context)


#######################
# Publication process #
#######################
class PublicationGrantsView(PermissionsMixin, UpdateView):
    """
    Add/update grants associated to a Publication.
    """
    permission_required = 'scipost.can_draft_publication'
    queryset = Publication.objects.drafts()
    slug_field = slug_url_kwarg = 'doi_label'
    form_class = PublicationGrantsForm
    template_name = 'journals/grants_form.html'


class PublicationGrantsRemovalView(PermissionsMixin, DetailView):
    """
    Remove grant associated to a Publication.
    """
    permission_required = 'scipost.can_draft_publication'
    queryset = Publication.objects.drafts()
    slug_field = slug_url_kwarg = 'doi_label'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        grant = get_object_or_404(Grant, id=kwargs.get('grant_id'))
        self.object.grants.remove(grant)
        return redirect(reverse('journals:update_grants', args=(self.object.doi_label,)))


class DraftPublicationUpdateView(PermissionsMixin, UpdateView):
    """
    Any Production Officer or Administrator can draft a new publication without publishing here.
    The actual publishing is done lin a later stadium, after the draft has been finished.
    """
    permission_required = 'scipost.can_draft_publication'
    queryset = Publication.objects.unpublished()
    slug_url_kwarg = 'arxiv_identifier_w_vn_nr'
    slug_field = 'accepted_submission__arxiv_identifier_w_vn_nr'
    form_class = DraftPublicationForm
    template_name = 'journals/publication_form.html'

    def get_object(self, queryset=None):
        try:
            publication = Publication.objects.get(
                accepted_submission__arxiv_identifier_w_vn_nr=self.kwargs.get(
                    'arxiv_identifier_w_vn_nr'))
        except Publication.DoesNotExist:
            if Submission.objects.accepted().filter(arxiv_identifier_w_vn_nr=self.kwargs.get(
              'arxiv_identifier_w_vn_nr')).exists():
                return None
            raise Http404('No accepted Submission found')
        if publication.status == STATUS_DRAFT:
            return publication
        if self.request.user.has_perm('scipost.can_publish_accepted_submission'):
            return publication
        raise Http404('Found Publication is not in draft')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['arxiv_identifier_w_vn_nr'] = self.kwargs.get('arxiv_identifier_w_vn_nr')
        kwargs['issue_id'] = self.request.GET.get('issue')
        return kwargs


class DraftPublicationApprovalView(PermissionsMixin, UpdateView):
    permission_required = 'scipost.can_draft_publication'
    queryset = Publication.objects.drafts()
    slug_field = slug_url_kwarg = 'doi_label'
    form_class = DraftPublicationApprovalForm
    template_name = 'journals/publication_approval_form.html'


@method_decorator(transaction.atomic, name='dispatch')
class PublicationPublishView(PermissionsMixin, RequestViewMixin, UpdateView):
    permission_required = 'scipost.can_publish_accepted_submission'
    queryset = Publication.objects.unpublished()
    slug_field = slug_url_kwarg = 'doi_label'
    form_class = PublicationPublishForm
    template_name = 'journals/publication_publish_form.html'


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def manage_metadata(request, issue_doi_label=None, doi_label=None):
    issues = Issue.objects.all().order_by('-until_date')
    publications = Publication.objects.all()
    if doi_label:
        issue_doi_label = issue_doi_label_from_doi_label(doi_label)
    if issue_doi_label:
        publications = publications.filter(in_issue__doi_label=issue_doi_label)
    publications = publications.order_by('-publication_date', '-paper_nr')
    associate_grant_form = GrantSelectForm()
    associate_generic_funder_form = FunderSelectForm()
    context = {
        'issues': issues,
        'issue_doi_label': issue_doi_label,
        'publications': publications,
        'associate_grant_form': associate_grant_form,
        'associate_generic_funder_form': associate_generic_funder_form,
    }
    return render(request, 'journals/manage_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_first_author(request, publication_id, author_object_id):
    publication = get_object_or_404(Publication, id=publication_id)
    author_object = get_object_or_404(publication.authors, id=author_object_id)

    # Redo ordering
    author_object.order = 1
    author_object.save()
    author_objects = publication.authors.exclude(id=author_object.id)
    count = 2
    for author in author_objects:
        author.order = count
        author.save()
        count += 1
    messages.success(request, 'Marked {} first author'.format(author_object))
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_draft_publication', return_403=True)
@transaction.atomic
def add_author(request, doi_label, contributor_id=None, unregistered_author_id=None):
    """
    If not all authors are registered Contributors or if they have not
    all claimed authorship, this method allows editorial administrators
    to associated them to the publication.
    This is important for the Crossref metadata, in which all authors must appear.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if not publication.is_draft and not request.user.has_perm('can_publish_accepted_submission'):
        raise Http404('You do not have permission to edit this non-draft Publication')

    if contributor_id:
        contributor = get_object_or_404(Contributor, id=contributor_id)
        PublicationAuthorsTable.objects.create(contributor=contributor, publication=publication)
        publication.save()
        messages.success(request, 'Added {} as an author.'.format(contributor))
        return redirect(reverse('journals:manage_metadata',
                                kwargs={'doi_label': publication.doi_label}))

    contributors_found = None
    form = UnregisteredAuthorForm(request.POST or request.GET or None)

    if request.POST and form.is_valid():
        unregistered_author = form.save()
        PublicationAuthorsTable.objects.create(
            publication=publication,
            unregistered_author=unregistered_author)
        messages.success(request, 'Added {} as an unregistered author.'.format(
            unregistered_author
        ))
        return redirect(reverse('journals:manage_metadata',
                                kwargs={'doi_label': publication.doi_label}))
    elif form.is_valid():
        contributors_found = Contributor.objects.filter(
            user__last_name__icontains=form.cleaned_data['last_name'])
    context = {
        'publication': publication,
        'contributors_found': contributors_found,
        'form': form,
    }
    return render(request, 'journals/add_author.html', context)


@permission_required('scipost.can_draft_publication', return_403=True)
def update_references(request, doi_label):
    """
    Update the References for a certain Publication.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if not publication.is_draft and not request.user.has_perm('can_publish_accepted_submission'):
        raise Http404('You do not have permission to edit this non-draft Publication')

    references = publication.references.all()
    formset = ReferenceFormSet(request.POST or None, queryset=references, publication=publication,
                               extra=request.GET.get('extra'))

    if request.GET.get('prefill'):
        formset.prefill()

    if formset.is_valid():
        formset.save()
        messages.success(request, 'References saved')
        return redirect(publication.get_absolute_url())

    context = {
        'publication': publication,
        'formset': formset,
    }
    return render(request, 'journals/update_references.html', context)


class CitationUpdateView(PublicationMixin, ProdSupervisorPublicationPermissionMixin, UpdateView):
    """
    Populates the citation_list dictionary entry in the metadata field in a Publication instance.
    """
    form_class = CitationListBibitemsForm
    template_name = 'journals/create_citation_list_metadata.html'


class FundingInfoView(PublicationMixin, ProdSupervisorPublicationPermissionMixin, UpdateView):
    """
    Add/update funding statement to the xml_metadata
    """
    form_class = FundingInfoForm
    template_name = 'journals/create_funding_info_metadata.html'


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def add_associated_grant(request, doi_label):
    """
    Called by an Editorial Administrator.
    This associates a grant from the database to this publication.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    grant_select_form = GrantSelectForm(request.POST or None)
    if grant_select_form.is_valid():
        publication.grants.add(grant_select_form.cleaned_data['grant'])
        publication.save()
        messages.success(request, 'Grant added to publication %s' % str(publication))
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def add_generic_funder(request, doi_label):
    """
    Called by an Editorial Administrator.
    This associates a funder (generic, not via grant) from the database to this publication.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    funder_select_form = FunderSelectForm(request.POST or None)
    if funder_select_form.is_valid():
        publication.funders_generic.add(funder_select_form.cleaned_data['funder'])
        publication.save()
        messages.success(request, 'Generic funder added to publication %s' % str(publication))
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': doi_label}))


class CreateMetadataXMLView(PublicationMixin,
                            ProdSupervisorPublicationPermissionMixin,
                            UpdateView):
    """
    To be called by an EdAdmin (or Production Supervisor) after the citation_list, funding_info
    entries have been filled. Populates the metadata_xml field of a Publication instance.
    The contents can then be sent to Crossref for registration.
    """
    form_class = CreateMetadataXMLForm
    template_name = 'journals/create_metadata_xml.html'


@permission_required('scipost.can_draft_publication', return_403=True)
@transaction.atomic
def metadata_xml_deposit(request, doi_label, option='test'):
    """
    Crossref metadata deposit.
    If test==True, test the metadata_xml using the Crossref test server.
    Makes use of the python requests module.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if not publication.is_draft and not request.user.has_perm('can_publish_accepted_submission'):
        raise Http404('You do not have permission to access this non-draft Publication')
    if not request.user.has_perm('can_publish_accepted_submission') and option != 'test':
        raise PermissionDenied('You do not have permission to do real Crossref deposits')

    if publication.metadata_xml is None:
        messages.warning(
            request,
            'This publication has no metadata. Produce it first before saving it.')
        return redirect(reverse('journals:create_metadata_xml',
                                kwargs={'doi_label': publication.doi_label}))

    timestamp = (publication.metadata_xml.partition(
        '<timestamp>'))[2].partition('</timestamp>')[0]
    doi_batch_id = (publication.metadata_xml.partition(
        '<doi_batch_id>'))[2].partition('</doi_batch_id>')[0]
    path = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
            + publication.get_paper_nr() + '/' + publication.doi_label.replace('.', '_')
            + '_Crossref_' + timestamp + '.xml')

    valid = True
    response_headers = None
    response_text = None
    if os.path.isfile(path):
        # Deposit already done before.
        valid = False
    else:
        # New deposit, go for it.
        if option == 'deposit' and not settings.DEBUG:
            # CAUTION: Real deposit only on production (non-debug-mode)
            url = 'http://doi.crossref.org/servlet/deposit'
        else:
            url = 'http://test.crossref.org/servlet/deposit'

        # First perform the actual deposit to Crossref
        params = {
            'operation': 'doMDUpload',
            'login_id': settings.CROSSREF_LOGIN_ID,
            'login_passwd': settings.CROSSREF_LOGIN_PASSWORD,
            }
        files = {
            'fname': ('metadata.xml',
                      publication.metadata_xml.encode('utf-8'),
                      'multipart/form-data')
        }
        r = requests.post(url, params=params, files=files)
        response_headers = r.headers
        response_text = r.text

        # Then create the associated Deposit object (saving the metadata to a file)
        if option == 'deposit':
            deposit = Deposit(publication=publication,
                              timestamp=timestamp,
                              doi_batch_id=doi_batch_id,
                              metadata_xml=publication.metadata_xml,
                              deposition_date=timezone.now())
            deposit.response_text = r.text

            # Save the filename with timestamp
            path_with_timestamp = '{issue}/{paper}/{doi}_Crossref_{timestamp}.xml'.format(
                issue=publication.in_issue.path,
                paper=publication.get_paper_nr(),
                doi=publication.doi_label.replace('.', '_'),
                timestamp=timestamp)
            f = open(settings.MEDIA_ROOT + path_with_timestamp, 'w', encoding='utf-8')
            f.write(publication.metadata_xml)
            f.close()

            # Copy file
            path_without_timestamp = '{issue}/{paper}/{doi}_Crossref.xml'.format(
                issue=publication.in_issue.path,
                paper=publication.get_paper_nr(),
                doi=publication.doi_label.replace('.', '_'))
            shutil.copyfile(settings.MEDIA_ROOT + path_with_timestamp,
                            settings.MEDIA_ROOT + path_without_timestamp)

            deposit.metadata_xml_file = path_with_timestamp
            deposit.save()
            publication.latest_crossref_deposit = timezone.now()
            publication.save()

    context = {
        'option': option,
        'publication': publication,
        'response_headers': response_headers,
        'response_text': response_text,
        'valid': valid,
    }
    return render(request, 'journals/metadata_xml_deposit.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_deposit_success(request, deposit_id, success):
    deposit = get_object_or_404(Deposit, pk=deposit_id)
    if success == '1':
        deposit.deposit_successful = True
    elif success == '0':
        deposit.deposit_successful = False
    deposit.save()
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': deposit.publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def produce_metadata_DOAJ(request, doi_label):
    publication = get_object_or_404(Publication, doi_label=doi_label)
    form = CreateMetadataDOAJForm(request.POST or None, instance=publication, request=request)
    if form.is_valid():
        form.save()
        messages.success(request, '<h3>%s</h3>Successfully produced metadata DOAJ.'
                                  % publication.doi_label)
        return redirect(reverse('journals:manage_metadata'))
    context = {
        'publication': publication,
        'form': form
    }
    return render(request, 'journals/metadata_doaj_create.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def metadata_DOAJ_deposit(request, doi_label):
    """
    DOAJ metadata deposit.
    Makes use of the python requests module.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)

    if not publication.metadata_DOAJ:
        messages.warning(request, '<h3>%s</h3>Failed: please first produce '
                                  'DOAJ metadata before depositing.' % publication.doi_label)
        return redirect(reverse('journals:manage_metadata'))

    timestamp = (publication.metadata_xml.partition(
        '<timestamp>'))[2].partition('</timestamp>')[0]
    path = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
            + publication.get_paper_nr() + '/' + publication.doi_label.replace('.', '_')
            + '_DOAJ_' + timestamp + '.json')
    if os.path.isfile(path):
        errormessage = 'The metadata file for this metadata timestamp already exists'
        return render(request, 'scipost/error.html', context={'errormessage': errormessage})

    url = 'https://doaj.org/api/v1/articles'
    params = {
        'api_key': settings.DOAJ_API_KEY,
    }
    try:
        r = requests.post(url, params=params, json=publication.metadata_DOAJ)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        messages.warning(request, '<h3>%s</h3>Failed: Post went wrong, response text: %s' % (
            publication.doi_label, r.text))

    # Then create the associated Deposit object (saving the metadata to a file)
    deposit = DOAJDeposit(publication=publication, timestamp=timestamp,
                          metadata_DOAJ=publication.metadata_DOAJ, deposition_date=timezone.now())
    deposit.response_text = r.text

    # Save a copy to the filename with and without timestamp
    path_with_timestamp = '{issue}/{paper}/{doi}_DOAJ_{timestamp}.json'.format(
        issue=publication.in_issue.path,
        paper=publication.get_paper_nr(),
        doi=publication.doi_label.replace('.', '_'),
        timestamp=timestamp)
    f = open(settings.MEDIA_ROOT + path_with_timestamp, 'w')
    f.write(json.dumps(publication.metadata_DOAJ))
    f.close()

    # Copy file
    path_without_timestamp = '{issue}/{paper}/{doi}_DOAJ.json'.format(
        issue=publication.in_issue.path,
        paper=publication.get_paper_nr(),
        doi=publication.doi_label.replace('.', '_'))
    shutil.copyfile(settings.MEDIA_ROOT + path_with_timestamp,
                    settings.MEDIA_ROOT + path_without_timestamp)

    # Save the database entry
    deposit.metadata_DOAJ_file = path_with_timestamp
    deposit.save()

    messages.success(request, '<h3>%s</h3>Successfull deposit of metadata DOAJ.'
                              % publication.doi_label)
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_doaj_deposit_success(request, deposit_id, success):
    deposit = get_object_or_404(DOAJDeposit, pk=deposit_id)
    if success == '1':
        deposit.deposit_successful = True
    elif success == '0':
        deposit.deposit_successful = False
    deposit.save()
    return redirect(reverse('journals:manage_metadata',
                    kwargs={'doi_label': deposit.publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def harvest_citedby_list(request):
    publications = Publication.objects.order_by('-publication_date')
    context = {
        'publications': publications
    }
    return render(request, 'journals/harvest_citedby_list.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def harvest_citedby_links(request, doi_label):
    publication = get_object_or_404(Publication, doi_label=doi_label)
    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode('utf8')
    idsalt = publication.title[:10]
    idsalt = idsalt.encode('utf8')
    doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()
    query_xml = ('<?xml version = "1.0" encoding="UTF-8"?>'
                 '<query_batch version="2.0" xmlns = "http://www.crossref.org/qschema/2.0"'
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
                 'xsi:schemaLocation="http://www.crossref.org/qschema/2.0 '
                 'http://www.crossref.org/qschema/crossref_query_input2.0.xsd">'
                 '<head>'
                 '<email_address>' + settings.CROSSREF_DEPOSIT_EMAIL + '</email_address>'
                 '<doi_batch_id>' + str(doi_batch_id) + '</doi_batch_id>'
                 '</head>'
                 '<body>'
                 '<fl_query alert="false">'
                 '<doi>' + publication.doi_string + '</doi>'
                 '</fl_query>'
                 '</body>'
                 '</query_batch>')
    url = 'http://doi.crossref.org/servlet/getForwardLinks'
    params = {'usr': settings.CROSSREF_LOGIN_ID,
              'pwd': settings.CROSSREF_LOGIN_PASSWORD,
              'qdata': query_xml,
              'doi': publication.doi_string, }
    r = requests.post(url, params=params)
    if r.status_code == 401:
        messages.warning(request, ('<h3>Crossref credentials are invalid.</h3>'
                                   'Please contact the SciPost Admin.'))
        return redirect(reverse('journals:manage_metadata',
                                kwargs={'doi_label': doi_label}))
    response_headers = r.headers
    response_text = r.text
    response_deserialized = ET.fromstring(r.text)
    prefix = '{http://www.crossref.org/qrschema/2.0}'
    citations = []
    for link in response_deserialized.iter(prefix + 'forward_link'):
        doi = link.find(prefix + 'journal_cite').find(prefix + 'doi').text
        article_title = link.find(prefix + 'journal_cite').find(prefix + 'article_title').text
        try:
            journal_abbreviation = link.find(prefix + 'journal_cite').find(
                prefix + 'journal_abbreviation').text
        except:
            journal_abbreviation = None
        try:
            volume = link.find(prefix + 'journal_cite').find(prefix + 'volume').text
        except AttributeError:
            volume = None
        try:
            first_page = link.find(prefix + 'journal_cite').find(prefix + 'first_page').text
        except:
            first_page = None
        try:
            item_number = link.find(prefix + 'journal_cite').find(prefix + 'item_number').text
        except:
            item_number = None
        multiauthors = False
        for author in link.find(prefix + 'journal_cite').find(
                prefix + 'contributors').iter(prefix + 'contributor'):
            if author.get('sequence') == 'first':
                first_author_given_name = author.find(prefix + 'given_name').text
                first_author_surname = author.find(prefix + 'surname').text
            else:
                multiauthors = True
        year = link.find(prefix + 'journal_cite').find(prefix + 'year').text
        citations.append({'doi': doi,
                          'article_title': article_title,
                          'journal_abbreviation': journal_abbreviation,
                          'first_author_given_name': first_author_given_name,
                          'first_author_surname': first_author_surname,
                          'multiauthors': multiauthors,
                          'volume': volume,
                          'first_page': first_page,
                          'item_number': item_number,
                          'year': year, })
    publication.citedby = citations
    publication.latest_citedby_update = timezone.now()
    publication.save()
    context = {
        'publication': publication,
        'response_headers': response_headers,
        'response_text': response_text,
        'response_deserialized': response_deserialized,
        'citations': citations,
    }
    return render(request, 'journals/harvest_citedby_links.html', context)


@login_required
def sign_existing_report(request, report_id):
    """
    Allows the author of a Report, originally submitted anonymously,
    to sign the Report.
    """
    report = get_object_or_404(Report, pk=report_id)
    if report.author != request.user.contributor:
        errormessage = 'Only the author of this Report can change its anonymity status'
        return render(request, 'scipost/error.html', context={'errormessage': errormessage})
    form = ConfirmationForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data['confirm'] == 'True':
            report.anonymous = False
            report.doideposit_needs_updating = True
            report.save()
            messages.success(request, 'Your Report is now publicly signed.')
        else:
            messages.error(request, 'Report signing operation cancelled.')
        return redirect(reverse('scipost:personal_page'))
    context = {'report': report, 'form': form}
    return render(request, 'journals/sign_existing_report.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def manage_report_metadata(request):
    """
    This page offers Editorial Administrators tools for managing
    the metadata of Reports.
    """
    reports = Report.objects.all()
    paginator = Paginator(reports, 25)

    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    context = {
        'reports': reports,
    }
    return render(request, 'journals/manage_report_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def manage_comment_metadata(request):
    """
    This page offers Editorial Administrators tools for managing
    the metadata of Comments.
    """
    comments = Comment.objects.all()
    context = {
        'comments': comments,
    }
    return render(request, 'journals/manage_comment_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_report_doi_needed(request, report_id, needed):
    report = get_object_or_404(Report, pk=report_id)
    if needed == '1':
        report.needs_doi = True
    elif needed == '0':
        report.needs_doi = False
    report.save()
    return redirect(reverse('journals:manage_report_metadata'))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_comment_doi_needed(request, comment_id, needed):
    comment = get_object_or_404(Comment, pk=comment_id)
    if needed == '1':
        comment.needs_doi = True
    elif needed == '0':
        comment.needs_doi = False
    comment.save()
    return redirect(reverse('journals:manage_comment_metadata'))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def generic_metadata_xml_deposit(request, **kwargs):
    """
    This method creates the metadata for non-Publication objects
    such as Reports and Comments, and deposits the metadata to
    Crossref.
    If there exists a relation to a SciPost-published object,
    the deposit uses Crossref's peer review content type.
    Otherwise the deposit is done as a dataset.
    """
    type_of_object = kwargs['type_of_object']
    object_id = int(kwargs['object_id'])

    if type_of_object == 'report':
        _object = get_object_or_404(Report, id=object_id)
    elif type_of_object == 'comment':
        _object = get_object_or_404(Comment, id=object_id)

    relation_to_published = _object.relation_to_published

    if not _object.doi_label:
        _object.create_doi_label()

    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode('utf8')
    idsalt = str(_object)[:10]
    idsalt = idsalt.encode('utf8')
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()
    metadata_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<doi_batch version="4.4.1" xmlns="http://www.crossref.org/schema/4.4.1" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.crossref.org/schema/4.4.1 '
        'http://www.crossref.org/shema/deposit/crossref4.4.1.xsd">\n'
        '<head>\n'
        '<doi_batch_id>' + str(doi_batch_id) + '</doi_batch_id>\n'
        '<timestamp>' + timestamp + '</timestamp>\n'
        '<depositor>\n'
        '<depositor_name>scipost</depositor_name>\n'
        '<email_address>' + settings.CROSSREF_DEPOSIT_EMAIL + '</email_address>\n'
        '</depositor>\n'
        '<registrant>scipost</registrant>\n'
        '</head>\n'
    )
    if relation_to_published:
        metadata_xml += (
            '<body>\n'
            '<peer_review stage="' + relation_to_published['stage'] + '">\n'
            '<contributors>'
        )
        if _object.anonymous:
            metadata_xml += (
                '<anonymous sequence="first" contributor_role="'
                + relation_to_published['contributor_role'] + '"/>'
            )
        else:
            metadata_xml += (
                '<person_name sequence="first" contributor_role="'
                + relation_to_published['contributor_role'] + '">'
                '<given_name>' + _object.author.user.first_name + '</given_name>'
                '<surname>' + _object.author.user.last_name + '</surname>'
                '</person_name>\n'
            )

        if isinstance(_object, Publication):
            url_to_declare = 'https://scipost.org{}'.format(_object.get_absolute_url())
        else:
            url_to_declare = 'https://scipost.org/{}'.format(_object.doi_label)

        metadata_xml += (
            '</contributors>\n'
            '<titles><title>' + relation_to_published['title'] + '</title></titles>\n'
            '<review_date>'
            '<month>' + _object.date_submitted.strftime('%m') + '</month>'
            '<day>' + _object.date_submitted.strftime('%d') + '</day>'
            '<year>' + _object.date_submitted.strftime('%Y') + '</year>'
            '</review_date>\n'
            '<program xmlns="http://www.crossref.org/relations.xsd">\n'
            '<related_item>'
            '<description>' + relation_to_published['title'] + '</description>\n'
            '<inter_work_relation relationship-type="isReviewOf" identifier-type="doi">'
            + relation_to_published['isReviewOfDOI'] + '</inter_work_relation></related_item>\n'
            '</program>'
            '<doi_data><doi>' + _object.doi_string + '</doi>\n'
            '<resource>' + url_to_declare +
            '</resource></doi_data>\n'
            '</peer_review>\n'
            '</body>\n'
            '</doi_batch>\n'
        )
    else:
        metadata_xml += (
            '<body>\n'
            '<database>\n'
            '<database_metadata language="en">\n'
            '<titles><title>SciPost Reports and Comments</title></titles>\n'
            '</database_metadata>\n'
            '<dataset dataset_type="collection">\n'
            '<doi_data><doi>' + _object.doi_string + '</doi>\n'
            '<resource>https://scipost.org' + _object.get_absolute_url() +
            '</resource></doi_data>\n'
            '</dataset></database>\n'
            '</body></doi_batch>'
        )

    if not settings.CROSSREF_DEBUG:
        # CAUTION: Debug is False, production goes for real deposit!!!
        url = 'http://doi.crossref.org/servlet/deposit'
    else:
        url = 'http://test.crossref.org/servlet/deposit'
    params = {
        'operation': 'doMDUpload',
        'login_id': settings.CROSSREF_LOGIN_ID,
        'login_passwd': settings.CROSSREF_LOGIN_PASSWORD,
        }
    files = {'fname': ('metadata.xml', metadata_xml, 'multipart/form-data')}
    r = requests.post(url, params=params, files=files)
    deposit = GenericDOIDeposit(content_type=ContentType.objects.get_for_model(_object),
                                object_id=object_id,
                                content_object=_object,
                                timestamp=timestamp,
                                doi_batch_id=doi_batch_id,
                                metadata_xml=metadata_xml,
                                deposition_date=timezone.now(),
                                response=r.text)
    deposit.save()
    context = {
        'response_headers': r.headers,
        'response_text': r.text,
    }
    return render(request, 'journals/generic_metadata_xml_deposit.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_generic_deposit_success(request, deposit_id, success):
    deposit = get_object_or_404(GenericDOIDeposit, pk=deposit_id)
    if success == '1':
        deposit.deposit_successful = True
        deposit.content_object.doideposit_needs_updating = False
        deposit.content_object.save()
    elif success == '0':
        deposit.deposit_successful = False
    deposit.save()
    if deposit.content_type.name == 'report':
        return redirect(reverse('journals:manage_report_metadata'))
    else:
        return redirect(reverse('journals:manage_comment_metadata'))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def email_object_made_citable(request, **kwargs):
    """
    This method sends an email to the author of a Report or a Comment,
    to notify that the object has been made citable (doi registered).
    """
    type_of_object = kwargs['type_of_object']
    object_id = int(kwargs['object_id'])

    if type_of_object == 'report':
        _object = get_object_or_404(Report, id=object_id)
        redirect_to = reverse('journals:manage_report_metadata')
        publication_citation = None
        publication_doi = None
        try:
            publication = Publication.objects.get(
                accepted_submission__arxiv_identifier_wo_vn_nr=_object.submission.arxiv_identifier_wo_vn_nr)
            publication_citation = publication.citation()
            publication_doi = publication.doi_string
        except Publication.DoesNotExist:
            pass
    elif type_of_object == 'comment':
        _object = get_object_or_404(Comment, id=object_id)
        redirect_to = reverse('journals:manage_comment_metadata')
    else:
        raise Http404

    if not _object.doi_label:
        messages.warning(request, 'This object does not have a DOI yet.')
        return redirect(redirect_to)

    if type_of_object == 'report':
        JournalUtils.load({'report': _object,
                           'publication_citation': publication_citation,
                           'publication_doi': publication_doi})
        JournalUtils.email_report_made_citable()
    else:
        JournalUtils.load({'comment': _object, })
        JournalUtils.email_comment_made_citable()
    messages.success(request, 'Email sent')
    return redirect(redirect_to)


###########
# Viewing #
###########

def report_detail(request, doi_label):
    report = get_object_or_404(Report.objects.accepted(), doi_label=doi_label)
    return redirect(report.get_absolute_url())


def comment_detail(request, doi_label):
    comment = get_object_or_404(Comment.objects.vetted().regular_comments(), doi_label=doi_label)
    return redirect(comment.get_absolute_url())


def author_reply_detail(request, doi_label):
    comment = get_object_or_404(Comment.objects.vetted().author_replies(), doi_label=doi_label)
    return redirect(comment.get_absolute_url())


def publication_detail(request, doi_label):
    """
    The actual Publication detail page. This is visible for everyone if published or
    visible for Production Supervisors and Administrators if in draft.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if not publication.is_published and not request.user.has_perm('scipost.can_draft_publication'):
        raise Http404('Publication is not publicly visible')

    journal = publication.in_issue.in_volume.in_journal

    context = {
        'publication': publication,
        'journal': journal
    }
    return render(request, 'journals/publication_detail.html', context)


def publication_detail_pdf(request, doi_label):
    """
    The actual Publication pdf. This is visible for everyone if published or
    visible for Production Supervisors and Administrators if in draft.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if not publication.is_published and not request.user.has_perm('scipost.can_draft_publication'):
        raise Http404('Publication is not publicly visible')

    response = HttpResponse(publication.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = ('filename='
                                       + publication.doi_label.replace('.', '_') + '.pdf')
    return response
