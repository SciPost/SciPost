import hashlib
import json
import os
import random
import requests
import string
import xml.etree.ElementTree as ET

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.http import HttpResponse

from .exceptions import PaperNumberingError
from .helpers import paper_nr_string, issue_doi_label_from_doi_label
from .models import Journal, Issue, Publication, UnregisteredAuthor, Deposit, DOAJDeposit,\
                    GenericDOIDeposit
from .forms import FundingInfoForm, InitiatePublicationForm, ValidatePublicationForm,\
                   UnregisteredAuthorForm, CreateMetadataXMLForm, CitationListBibitemsForm
from .utils import JournalUtils

from comments.models import Comment
from funders.models import Funder
from submissions.models import Submission, Report
from scipost.models import Contributor
from production.constants import PROOFS_PUBLISHED
from production.models import ProductionEvent
from production.signals import notify_stream_status_change

from funders.forms import FunderSelectForm, GrantSelectForm
from scipost.forms import ConfirmationForm

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
    recent_papers = Publication.objects.published(
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

    papers = issue.publication_set.order_by('paper_nr')
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

@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def initiate_publication(request):
    """
    Called by an Editorial Administrator.
    Publish the manuscript after proofs have been accepted.
    This method prefills a ValidatePublicationForm for further
    processing (verification in validate_publication method).
    """
    initiate_publication_form = InitiatePublicationForm(request.POST or None)
    if initiate_publication_form.is_valid():
        submission = initiate_publication_form.cleaned_data['accepted_submission']
        current_issue = initiate_publication_form.cleaned_data['to_be_issued_in']

        # Determine next available paper number:
        paper_nr = Publication.objects.filter(in_issue__in_volume=current_issue.in_volume).count()
        paper_nr += 1
        if paper_nr > 999:
            raise PaperNumberingError(paper_nr)

        # Build form data
        doi_label = (
            current_issue.in_volume.in_journal.name
            + '.' + str(current_issue.in_volume.number)
            + '.' + str(current_issue.number) + '.' + paper_nr_string(paper_nr)
        )
        doi_string = '10.21468/' + doi_label
        BiBTeX_entry = (
            '@Article{' + doi_label + ',\n'
            '\ttitle={{' + submission.title + '}},\n'
            '\tauthor={' + submission.author_list.replace(',', ' and') + '},\n'
            '\tjournal={'
            + current_issue.in_volume.in_journal.get_abbreviation_citation()
            + '},\n'
            '\tvolume={' + str(current_issue.in_volume.number) + '},\n'
            '\tissue={' + str(current_issue.number) + '},\n'
            '\tpages={' + paper_nr_string(paper_nr) + '},\n'
            '\tyear={' + current_issue.until_date.strftime('%Y') + '},\n'
            '\tpublisher={SciPost},\n'
            '\tdoi={' + doi_string + '},\n'
            '\turl={https://scipost.org/' + doi_string + '},\n'
            '}\n'
        )
        initial = {
            'accepted_submission': submission,
            'in_issue': current_issue,
            'paper_nr': paper_nr,
            'discipline': submission.discipline,
            'domain': submission.domain,
            'subject_area': submission.subject_area,
            'secondary_areas': submission.secondary_areas,
            'title': submission.title,
            'author_list': submission.author_list,
            'abstract': submission.abstract,
            'BiBTeX_entry': BiBTeX_entry,
            'doi_label': doi_label,
            'acceptance_date': submission.acceptance_date,
            'submission_date': submission.submission_date,
            'publication_date': timezone.now(),
        }
        validate_publication_form = ValidatePublicationForm(initial=initial)
        context = {'validate_publication_form': validate_publication_form}
        return render(request, 'journals/validate_publication.html', context)

    context = {'initiate_publication_form': initiate_publication_form}
    return render(request, 'journals/initiate_publication.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def validate_publication(request):
    """
    This creates a Publication instance from the ValidatePublicationForm,
    pre-filled by the initiate_publication method above.
    """
    # TODO: move from uploads to Journal folder
    # TODO: create metadata
    # TODO: set DOI, register with Crossref
    # TODO: add funding info
    context = {}
    validate_publication_form = ValidatePublicationForm(request.POST or None,
                                                        request.FILES or None)
    if validate_publication_form.is_valid():
        publication = validate_publication_form.save()

        # Fill in remaining data
        submission = publication.accepted_submission
        publication.authors.add(*submission.authors.all())
        if publication.first_author:
            publication.authors.add(publication.first_author)
        if publication.first_author_unregistered:
            publication.authors_unregistered.add(publication.first_author_unregistered)
        publication.authors_claims.add(*submission.authors_claims.all())
        publication.authors_false_claims.add(*submission.authors_false_claims.all())

        # Add Institutions to the publication
        for author in publication.authors.all():
            for current_affiliation in author.affiliations.active():
                publication.institutions.add(current_affiliation.institution)

        # Save the beast
        publication.save()

        # Move file to final location
        initial_path = publication.pdf_file.path
        new_dir = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
                   + publication.get_paper_nr())
        new_path = new_dir + '/' + publication.doi_label.replace('.', '_') + '.pdf'
        os.makedirs(new_dir)
        os.rename(initial_path, new_path)
        publication.pdf_file.name = new_path
        publication.save()

        # Mark the submission as having been published:
        submission.published_as = publication
        submission.status = 'published'
        submission.save()

        # Update ProductionStream
        stream = submission.production_stream
        if stream:
            stream.status = PROOFS_PUBLISHED
            stream.save()
            if request.user.production_user:
                prodevent = ProductionEvent(
                    stream=stream,
                    event='status',
                    comments=' published the manuscript.',
                    noted_by=request.user.production_user
                )
                prodevent.save()
            notify_stream_status_change(request.user, stream, False)

        # TODO: Create a Commentary Page
        # Email authors
        JournalUtils.load({'publication': publication})
        JournalUtils.send_authors_paper_published_email()

        # Add SubmissionEvents
        submission.add_general_event('The Submission has been published as %s.'
                                     % publication.doi_label)

        messages.success(request, 'The publication has been validated.')
        return redirect(publication.get_absolute_url())
    else:
        context['errormessage'] = 'The form was invalid.'

    context['validate_publication_form'] = validate_publication_form
    return render(request, 'journals/validate_publication.html', context)


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
@transaction.atomic
def mark_first_author(request, publication_id, contributor_id):
    publication = get_object_or_404(Publication, id=publication_id)
    contributor = get_object_or_404(Contributor, id=contributor_id)
    publication.first_author = contributor
    publication.first_author_unregistered = None
    publication.save()
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def mark_first_author_unregistered(request, publication_id, unregistered_author_id):
    publication = get_object_or_404(Publication, id=publication_id)
    unregistered_author = get_object_or_404(UnregisteredAuthor, id=unregistered_author_id)
    publication.first_author = None
    publication.first_author_unregistered = unregistered_author
    publication.save()
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def add_author(request, publication_id, contributor_id=None, unregistered_author_id=None):
    """
    If not all authors are registered Contributors or if they have not
    all claimed authorship, this method allows editorial administrators
    to associated them to the publication.
    This is important for the Crossref metadata, in which all authors must appear.
    """
    publication = get_object_or_404(Publication, id=publication_id)
    if contributor_id:
        contributor = get_object_or_404(Contributor, id=contributor_id)
        publication.authors.add(contributor)
        publication.save()
        return redirect(reverse('journals:manage_metadata',
                                kwargs={'doi_label': publication.doi_label}))

    if request.method == 'POST':
        form = UnregisteredAuthorForm(request.POST)
        if form.is_valid():
            contributors_found = Contributor.objects.filter(
                user__last_name__icontains=form.cleaned_data['last_name'])
            unregistered_authors_found = UnregisteredAuthor.objects.filter(
                last_name__icontains=form.cleaned_data['last_name'])
            new_unreg_author_form = UnregisteredAuthorForm(
                initial={'first_name': form.cleaned_data['first_name'],
                         'last_name': form.cleaned_data['last_name'], })
        else:
            errormessage = 'Please fill in the form properly'
            return render(request, 'scipost/error.html', context={'errormessage': errormessage})
    else:
        form = UnregisteredAuthorForm()
        contributors_found = None
        unregistered_authors_found = None
        new_unreg_author_form = UnregisteredAuthorForm()
    context = {'publication': publication,
               'contributors_found': contributors_found,
               'unregistered_authors_found': unregistered_authors_found,
               'form': form,
               'new_unreg_author_form': new_unreg_author_form, }
    return render(request, 'journals/add_author.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def add_unregistered_author(request, publication_id, unregistered_author_id):
    publication = get_object_or_404(Publication, id=publication_id)
    unregistered_author = get_object_or_404(UnregisteredAuthor, id=unregistered_author_id)
    publication.authors_unregistered.add(unregistered_author)
    publication.save()
    return redirect(reverse('journals:manage_metadata',
                            kwargs={'doi_label': publication.doi_label}))


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def add_new_unreg_author(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    if request.method == 'POST':
        new_unreg_author_form = UnregisteredAuthorForm(request.POST)
        if new_unreg_author_form.is_valid():
            new_unreg_author = new_unreg_author_form.save()
            publication.authors_unregistered.add(new_unreg_author)
            return redirect(reverse('journals:manage_metadata',
                                    kwargs={'doi_label': publication.doi_label}))
    raise Http404


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_citation_list_metadata(request, doi_label):
    """
    Called by an Editorial Administrator.
    This populates the citation_list dictionary entry
    in the metadata field in a Publication instance.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if request.method == 'POST':
        bibitems_form = CitationListBibitemsForm(request.POST, request.FILES)
        if bibitems_form.is_valid():
            publication.metadata['citation_list'] = bibitems_form.extract_dois()
            publication.save()
    bibitems_form = CitationListBibitemsForm()
    context = {
        'publication': publication,
        'bibitems_form': bibitems_form,
    }
    if request.method == 'POST':
        context['citation_list'] = publication.metadata['citation_list']
    return render(request, 'journals/create_citation_list_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_funding_info_metadata(request, doi_label):
    """
    Called by an Editorial Administrator.
    This populates the funding_info dictionary entry
    in the metadata field in a Publication instance.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)

    funding_info_form = FundingInfoForm(request.POST or None)
    if funding_info_form.is_valid():
        publication.metadata['funding_statement'] = funding_info_form.cleaned_data[
                                                        'funding_statement']
        publication.save()

    try:
        initial = {'funding_statement': publication.metadata['funding_statement']}
        funding_statement = initial['funding_statement']
    except KeyError:
        initial = {'funding_statement': ''}
        funding_statement = ''

    context = {'publication': publication,
               'funding_info_form': FundingInfoForm(initial=initial),
               'funding_statement': funding_statement}

    return render(request, 'journals/create_funding_info_metadata.html', context)


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


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_metadata_xml(request, doi_label):
    """
    To be called by an EdAdmin after the citation_list,
    funding_info entries have been filled.
    Populates the metadata_xml field of a Publication instance.
    The contents can then be sent to Crossref for registration.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)

    create_metadata_xml_form = CreateMetadataXMLForm(request.POST or None, instance=publication)
    if create_metadata_xml_form.is_valid():
        create_metadata_xml_form.save()
        messages.success(request, 'Metadata XML saved')
        return redirect(reverse('journals:manage_metadata',
                                kwargs={'doi_label': doi_label}))

    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode('utf8')
    idsalt = publication.title[:10]
    idsalt = idsalt.encode('utf8')
    doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()

    initial = {'metadata_xml': ''}
    initial['metadata_xml'] += (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<doi_batch version="4.4.0" xmlns="http://www.crossref.org/schema/4.4.0" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:fr="http://www.crossref.org/fundref.xsd" '
        'xsi:schemaLocation="http://www.crossref.org/schema/4.4.0 '
        'http://www.crossref.org/shema/deposit/crossref4.4.0.xsd" '
        'xmlns:ai="http://www.crossref.org/AccessIndicators.xsd">\n'
        '<head>\n'
        '<doi_batch_id>' + str(doi_batch_id) + '</doi_batch_id>\n'
        '<timestamp>' + timezone.now().strftime('%Y%m%d%H%M%S') + '</timestamp>\n'
        '<depositor>\n'
        '<depositor_name>scipost</depositor_name>\n'
        '<email_address>admin@scipost.org</email_address>\n'
        '</depositor>\n'
        '<registrant>scipost</registrant>\n'
        '</head>\n'
        '<body>\n'
        '<journal>\n'
        '<journal_metadata>\n'
        '<full_title>' + publication.in_issue.in_volume.in_journal.get_name_display()
        + '</full_title>\n'
        '<abbrev_title>'
        + publication.in_issue.in_volume.in_journal.get_abbreviation_citation() +
        '</abbrev_title>\n'
        '<issn media_type=\'electronic\'>' + publication.in_issue.in_volume.in_journal.issn
        + '</issn>\n'
        '<doi_data>\n'
        '<doi>' + publication.in_issue.in_volume.in_journal.doi_string + '</doi>\n'
        '<resource>https://scipost.org/'
        + publication.in_issue.in_volume.in_journal.doi_string + '</resource>\n'
        '</doi_data>\n'
        '</journal_metadata>\n'
        '<journal_issue>\n'
        '<publication_date media_type=\'online\'>\n'
        '<year>' + publication.publication_date.strftime('%Y') + '</year>\n'
        '</publication_date>\n'
        '<journal_volume>\n'
        '<volume>' + str(publication.in_issue.in_volume.number) + '</volume>\n'
        '</journal_volume>\n'
        '<issue>' + str(publication.in_issue.number) + '</issue>\n'
        '</journal_issue>\n'
        '<journal_article publication_type=\'full_text\'>\n'
        '<titles><title>' + publication.title + '</title></titles>\n'
        '<contributors>\n'
    )

    # Precondition: all authors MUST be listed in authors field of publication instance,
    # this to be checked by EdAdmin before publishing.
    for author in publication.authors.all():
        if author == publication.first_author:
            initial['metadata_xml'] += (
                '<person_name sequence=\'first\' contributor_role=\'author\'> '
                '<given_name>' + author.user.first_name + '</given_name> '
                '<surname>' + author.user.last_name + '</surname> '
            )
        else:
            initial['metadata_xml'] += (
                '<person_name sequence=\'additional\' contributor_role=\'author\'> '
                '<given_name>' + author.user.first_name + '</given_name> '
                '<surname>' + author.user.last_name + '</surname> '
            )
        if author.orcid_id:
            initial['metadata_xml'] += '<ORCID>http://orcid.org/' + author.orcid_id + '</ORCID>'
        initial['metadata_xml'] += '</person_name>\n'

    for author_unreg in publication.authors_unregistered.all():
        if author_unreg == publication.first_author_unregistered:
            initial['metadata_xml'] += (
                '<person_name sequence=\'first\' contributor_role=\'author\'> '
                '<given_name>' + author_unreg.first_name + '</given_name> '
                '<surname>' + author_unreg.last_name + '</surname> '
            )
        else:
            initial['metadata_xml'] += (
                '<person_name sequence=\'additional\' contributor_role=\'author\'> '
                '<given_name>' + author_unreg.first_name + '</given_name> '
                '<surname>' + author_unreg.last_name + '</surname> '
            )
        initial['metadata_xml'] += '</person_name>\n'
    initial['metadata_xml'] += '</contributors>\n'

    initial['metadata_xml'] += (
        '<publication_date media_type=\'online\'>\n'
        '<month>' + publication.publication_date.strftime('%m') + '</month>'
        '<day>' + publication.publication_date.strftime('%d') + '</day>'
        '<year>' + publication.publication_date.strftime('%Y') + '</year>'
        '</publication_date>\n'
        '<publisher_item><item_number item_number_type="article_number">'
        + paper_nr_string(publication.paper_nr) +
        '</item_number></publisher_item>\n'
        '<crossmark>\n'
        '<crossmark_policy>10.21468/SciPost.CrossmarkPolicy</crossmark_policy>\n'
        '<crossmark_domains>\n'
        '<crossmark_domain><domain>scipost.org</domain></crossmark_domain>\n'
        '</crossmark_domains>\n'
        '<crossmark_domain_exclusive>false</crossmark_domain_exclusive>\n'
        )
    funders = (Funder.objects.filter(grant__in=publication.grants.all())
               | publication.funders_generic.all()).distinct()
    nr_funders = funders.count()
    initial['metadata_xml'] += '<custom_metadata>\n'
    if nr_funders > 0:
        initial['metadata_xml'] += '<fr:program name="fundref">\n'
        for funder in funders:
            if nr_funders > 1:
                initial['metadata_xml'] += '<fr:assertion name="fundgroup">\n'
            initial['metadata_xml'] += (
                '<fr:assertion name="funder_name">' + funder.name + '\n'
                '<fr:assertion name="funder_identifier">'
                + funder.identifier + '</fr:assertion>\n'
                '</fr:assertion>\n')
            for grant in publication.grants.all():
                if grant.funder == funder:
                    initial['metadata_xml'] += (
                        '<fr:assertion name="award_number">'
                        + grant.number + '</fr:assertion>\n')
            if nr_funders > 1:
                initial['metadata_xml'] += '</fr:assertion>\n'
        initial['metadata_xml'] += '</fr:program>\n'
    initial['metadata_xml'] += (
        '<ai:program name="AccessIndicators">\n'
        '<ai:license_ref>' + publication.get_cc_license_URI() +
        '</ai:license_ref>\n'
        '</ai:program>\n'
    )
    initial['metadata_xml'] += '</custom_metadata>\n'
    initial['metadata_xml'] += (
        '</crossmark>\n'
        '<archive_locations><archive name="CLOCKSS"></archive></archive_locations>\n'
        '<doi_data>\n'
        '<doi>' + publication.doi_string + '</doi>\n'
        '<resource>https://scipost.org/' + publication.doi_string + '</resource>\n'
        '<collection property="crawler-based">\n'
        '<item crawler="iParadigms">\n'
        '<resource>https://scipost.org/'
        + publication.doi_string + '/pdf</resource>\n'
        '</item></collection>\n'
        '<collection property="text-mining">\n'
        '<item><resource mime_type="application/pdf">'
        'https://scipost.org/' + publication.doi_string + '/pdf</resource></item>\n'
        '</collection>'
        '</doi_data>\n'
    )
    try:
        if publication.metadata['citation_list']:
            initial['metadata_xml'] += '<citation_list>\n'
            for ref in publication.metadata['citation_list']:
                initial['metadata_xml'] += (
                    '<citation key="' + ref['key'] + '">'
                    '<doi>' + ref['doi'] + '</doi>'
                    '</citation>\n'
                )
        initial['metadata_xml'] += '</citation_list>\n'
    except KeyError:
        pass
    initial['metadata_xml'] += (
        '</journal_article>\n'
        '</journal>\n'
    )
    initial['metadata_xml'] += '</body>\n</doi_batch>'

    publication.latest_metadata_update = timezone.now()
    publication.save()
    context = {
        'publication': publication,
        'create_metadata_xml_form': CreateMetadataXMLForm(initial=initial, instance=publication),
    }
    return render(request, 'journals/create_metadata_xml.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def metadata_xml_deposit(request, doi_label, option='test'):
    """
    Crossref metadata deposit.
    If test==True, test the metadata_xml using the Crossref test server.
    Makes use of the python requests module.
    """
    publication = get_object_or_404(Publication, doi_label=doi_label)
    timestamp = (publication.metadata_xml.partition(
        '<timestamp>'))[2].partition('</timestamp>')[0]
    doi_batch_id = (publication.metadata_xml.partition(
        '<doi_batch_id>'))[2].partition('</doi_batch_id>')[0]
    path = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
            + publication.get_paper_nr() + '/' + publication.doi_label.replace('.', '_')
            + '_Crossref_' + timestamp + '.xml')
    if os.path.isfile(path):
        errormessage = 'The metadata file for this metadata timestamp already exists'
        return render(request, 'scipost/error.html', context={'errormessage': errormessage})
    if option == 'deposit' and not settings.DEBUG:
        # CAUTION: Real deposit only on production (non-debug-mode)
        url = 'http://doi.crossref.org/servlet/deposit'
    else:
        url = 'http://test.crossref.org/servlet/deposit'

    if publication.metadata_xml is None:
        errormessage = 'This publication has no metadata. Produce it first before saving it.'
        return render(request, 'scipost/error.html', context={'errormessage': errormessage})
    # First perform the actual deposit to Crossref
    params = {
        'operation': 'doMDUpload',
        'login_id': settings.CROSSREF_LOGIN_ID,
        'login_passwd': settings.CROSSREF_LOGIN_PASSWORD,
        }
    files = {'fname': ('metadata.xml', publication.metadata_xml, 'multipart/form-data')}
    r = requests.post(url, params=params, files=files)
    response_headers = r.headers
    response_text = r.text

    # Then create the associated Deposit object (saving the metadata to a file)
    if option == 'deposit':
        content = ContentFile(publication.metadata_xml)
        deposit = Deposit(publication=publication, timestamp=timestamp, doi_batch_id=doi_batch_id,
                          metadata_xml=publication.metadata_xml, deposition_date=timezone.now())
        deposit.metadata_xml_file.save(path, content)
        deposit.response_text = r.text
        deposit.save()
        publication.latest_crossref_deposit = timezone.now()
        publication.save()
        # Save a copy to the filename without timestamp
        path1 = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
                 + publication.get_paper_nr() + '/' + publication.doi_label.replace('.', '_')
                 + '_Crossref.xml')
        f = open(path1, 'w')
        f.write(publication.metadata_xml)
        f.close()

    context = {
        'option': option,
        'publication': publication,
        'response_headers': response_headers,
        'response_text': response_text,
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
    JournalUtils.load({'request': request, 'publication': publication})
    publication.metadata_DOAJ = JournalUtils.generate_metadata_DOAJ()
    publication.save()
    messages.success(request, '<h3>%s</h3>Successfully produced metadata DOAJ.'
                              % publication.doi_label)
    return redirect(reverse('journals:manage_metadata'))


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
    content = ContentFile(json.dumps(publication.metadata_DOAJ))
    deposit = DOAJDeposit(publication=publication, timestamp=timestamp,
                          metadata_DOAJ=publication.metadata_DOAJ, deposition_date=timezone.now())
    deposit.metadata_DOAJ_file.save(path, content)
    deposit.response_text = r.text
    deposit.save()

    # Save a copy to the filename without timestamp
    path1 = (settings.MEDIA_ROOT + publication.in_issue.path + '/'
             + publication.get_paper_nr() + '/' + publication.doi_label.replace('.', '_')
             + '_DOAJ.json')
    f = open(path1, 'w')
    f.write(json.dumps(publication.metadata_DOAJ))
    f.close()

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
                 '<email_address>admin@scipost.org</email_address>'
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
    """
    type_of_object = kwargs['type_of_object']
    object_id = int(kwargs['object_id'])
    if type_of_object == 'report':
        _object = get_object_or_404(Report, id=object_id)
    elif type_of_object == 'comment':
        _object = get_object_or_404(Comment, id=object_id)

    if not _object.doi_label:
        _object.create_doi_label()

    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode('utf8')
    idsalt = str(_object)[:10]
    idsalt = idsalt.encode('utf8')
    timestamp=timezone.now().strftime('%Y%m%d%H%M%S')
    doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()
    metadata_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<doi_batch version="4.4.0" xmlns="http://www.crossref.org/schema/4.4.0" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:fr="http://www.crossref.org/fundref.xsd" '
        'xsi:schemaLocation="http://www.crossref.org/schema/4.4.0 '
        'http://www.crossref.org/shema/deposit/crossref4.4.0.xsd" '
        'xmlns:ai="http://www.crossref.org/AccessIndicators.xsd">\n'
        '<head>\n'
        '<doi_batch_id>' + str(doi_batch_id) + '</doi_batch_id>\n'
        '<timestamp>' + timestamp + '</timestamp>\n'
        '<depositor>\n'
        '<depositor_name>scipost</depositor_name>\n'
        '<email_address>admin@scipost.org</email_address>\n'
        '</depositor>\n'
        '<registrant>scipost</registrant>\n'
        '</head>\n'
        '<body>\n'
        '<database>\n'
        '<database_metadata language="en">\n'
        '<titles><title>SciPost Reports and Comments</title></titles>\n'
        '</database_metadata>\n'
        '<dataset dataset_type="collection">\n'
        '<doi_data><doi>' + _object.doi_string + '</doi>\n'
        '<resource>https://scipost.org' + _object.get_absolute_url() + '</resource></doi_data>\n'
        '</dataset></database>\n'
        '</body></doi_batch>'
        )
    if not settings.DEBUG:
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


###########
# Viewing #
###########

def publication_detail(request, doi_label):
    publication = Publication.objects.get_published(doi_label=doi_label)
    journal = publication.in_issue.in_volume.in_journal

    context = {
        'publication': publication,
        'journal': journal
    }
    return render(request, 'journals/publication_detail.html', context)


def publication_detail_pdf(request, doi_label):
    publication = Publication.objects.get_published(doi_label=doi_label)
    response = HttpResponse(publication.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = ('filename='
                                       + publication.doi_label.replace('.', '_') + '.pdf')
    return response
