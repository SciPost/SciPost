import datetime
import hashlib
import os
import random
import requests
import string

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files import File
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from journals.utils import JournalUtils

from submissions.models import SUBMISSION_STATUS_PUBLICLY_UNLISTED
from submissions.models import Submission

from guardian.decorators import permission_required
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm

############
# Journals 
############


# Utilities


# @permission_required('scipost.can_publish_accepted_submission', return_403=True)
# @transaction.atomic
# def open_new_issue(request):
#     """
#     For a Journal/Volume, creates a new issue.
#     """
    
#     settings.JOURNALS_DIR 
#     + journal_name_abbrev_doi(publication.in_issue.in_volume.in_journal.name)
#     + '/' + str(publication.in_issue.in_volume.number)
#     + '/' + str(publication.in_issue.number)


def journals(request):
    return render(request, 'journals/journals.html')


def scipost_physics(request):
    #issues = Issue.objects.filter(
    #    in_volume__in_journal__name='SciPost Physics').order_by('-until_date')
    current_issue = Issue.objects.filter(
        in_volume__in_journal__name='SciPost Physics',
        start_date__lte=timezone.now(),
        until_date__gte=timezone.now()).order_by('-until_date').first()
    latest_issue = Issue.objects.filter(
        in_volume__in_journal__name='SciPost Physics',
        until_date__lte=timezone.now()).order_by('-until_date').first()
    #recent_papers = Publication.objects.filter(
    #    #in_issue=latest_issue).order_by('paper_nr')
    #    in_issue__in_volume__in_journal__name='SciPost Physics').order_by('-publication_date')[:20]
    #accepted_SP_submissions = Submission.objects.filter(
    #    submitted_to_journal='SciPost Physics', status='accepted'
    #).order_by('-latest_activity')
    #current_SP_submissions = Submission.objects.filter(
    #    submitted_to_journal='SciPost Physics'
    #    ).exclude(status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED
    #    ).order_by('-submission_date')
    context = {
        #'issues': issues, 
        'current_issue': current_issue,
        'latest_issue': latest_issue,
        #'recent_papers': recent_papers,
        #'accepted_SP_submissions': accepted_SP_submissions,
        #'current_SP_submissions': current_SP_submissions,
    }
    return render(request, 'journals/scipost_physics.html', context)


def scipost_physics_issues(request):
    issues = Issue.objects.filter(
        in_volume__in_journal__name='SciPost Physics').order_by('-until_date')
    context = {'issues': issues,}
    return render(request, 'journals/scipost_physics_issues.html', context)


def scipost_physics_recent(request):
    """
    Display page for the most recent 20 publications in SciPost Physics.
    """
    #latest_issue = Issue.objects.filter(
    #    in_volume__in_journal__name='SciPost Physics').order_by('-until_date').first()
    recent_papers = Publication.objects.filter(
        #in_issue=latest_issue).order_by('-publication_date')
        in_issue__in_volume__in_journal__name='SciPost Physics').order_by('-publication_date')[:20]
    context = {#'latest_issue': latest_issue,
               'recent_papers': recent_papers}
    return render(request, 'journals/scipost_physics_recent.html', context)


def scipost_physics_accepted(request):
    """
    Display page for submissions to SciPost Physics which
    have been accepted but are not yet published.
    """
    accepted_SP_submissions = Submission.objects.filter(
        submitted_to_journal='SciPost Physics', status='accepted'
    ).order_by('-latest_activity')
    context = {'accepted_SP_submissions': accepted_SP_submissions}
    return render(request, 'journals/scipost_physics_accepted.html', context)


# def scipost_physics_submissions(request):
#     """
#     Display page for submissions to SciPost Physics which
#     have been accepted but are not yet published.
#     """
#     current_SP_submissions = Submission.objects.filter(
#         submitted_to_journal='SciPost Physics'
#         ).exclude(status__in=SUBMISSION_STATUS_PUBLICLY_UNLISTED
#         ).order_by('-submission_date')
#     context = {'current_SP_submissions': current_SP_submissions}
#     return render(request, 'journals/scipost_physics_submissions.html', context)


def scipost_physics_info_for_authors(request):
    return render(request, 'journals/scipost_physics_info_for_authors.html')


def scipost_physics_about(request):
    return render(request, 'journals/scipost_physics_about.html')



def scipost_physics_issue_detail(request, volume_nr, issue_nr):
    issue = get_object_or_404 (Issue, in_volume__in_journal__name='SciPost Physics',
                               number=issue_nr)
    papers = issue.publication_set.order_by('paper_nr')
    context = {'issue': issue, 'papers': papers}
    return render(request, 'journals/scipost_physics_issue_detail.html', context)


def upload_proofs(request):
    """ 
    TODO
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    return render(request, 'journals/upload_proofs.html')


#######################
# Publication process #
#######################

# @permission_required('scipost.can_publish_accepted_submission', return_403=True)
# @transaction.atomic
# def publishing_workspace(request):
#     """
#     Page containing post-acceptance publishing workflow items.
#     """
#     accepted_submissions = Submission.objects.filter(status='accepted')
#     context = {'accepted_submissions': accepted_submissions,}
#     return render(request, 'journals/publishing_workspace.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def initiate_publication(request):
    """
    Called by an Editorial Administrator.
    Publish the manuscript after proofs have been accepted.
    This method prefills a ValidatePublicationForm for further
    processing (verification in validate_publication method).
    """
    if request.method == 'POST':
        initiate_publication_form = InitiatePublicationForm(request.POST)
        if initiate_publication_form.is_valid():
            submission = get_object_or_404(Submission, 
                pk=initiate_publication_form.cleaned_data['accepted_submission'].id)
            current_issue = get_object_or_404(Issue, 
                            pk=initiate_publication_form.cleaned_data['to_be_issued_in'].id)
            # Determine next available paper number:
            papers_in_current_issue = Publication.objects.filter(in_issue=current_issue)
            paper_nr = 1
            while papers_in_current_issue.filter(paper_nr=paper_nr).exists():
                paper_nr += 1
                if paper_nr > 999:
                    raise PaperNumberingError(paper_nr)
            doi_label = (
                journal_name_abbrev_doi(current_issue.in_volume.in_journal.name)
                + '.' + str(current_issue.in_volume.number)
                + '.' + str(current_issue.number) + '.' + paper_nr_string(paper_nr)
            )
            doi_string='10.21468/' + doi_label
            BiBTeX_entry = (
                '@Article{' + doi_label + ',\n'
                '\ttitle={{' + submission.title + '}},\n'
                '\tauthor={' + submission.author_list.replace(',', ' and') + '},\n'
                '\tjournal={' 
                + journal_name_abbrev_citation(current_issue.in_volume.in_journal.name)
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
                'doi_string': doi_string,
                'submission_date': initiate_publication_form.cleaned_data['original_submission_date'],
                'acceptance_date': initiate_publication_form.cleaned_data['acceptance_date'],
                'publication_date': timezone.now(),
                'latest_activity': timezone.now(),
            }
            validate_publication_form = ValidatePublicationForm(initial=initial)
            context = {'validate_publication_form': validate_publication_form,}
            return render(request, 'journals/validate_publication.html', context)
        else:
            errormessage = 'The form was not filled validly.'
            context = {'initiate_publication_form': initiate_publication_form,
                       'errormessage': errormessage}
            return render(request, 'journals/initiate_publication.html', context)
    else:
        initiate_publication_form = InitiatePublicationForm()
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
    if request.method == 'POST':
        validate_publication_form = ValidatePublicationForm(request.POST, request.FILES)
        if validate_publication_form.is_valid():
            publication = validate_publication_form.save()
            # Fill in remaining data
            publication.pdf_file = request.FILES['pdf_file']
            submission = publication.accepted_submission
            publication.authors.add(*submission.authors.all())
            publication.authors_claims.add(*submission.authors_claims.all())
            publication.authors_false_claims.add(*submission.authors_false_claims.all())
            publication.save()
            # Move file to final location
            initial_path = publication.pdf_file.path
            new_dir =  (publication.in_issue.path
                        + paper_nr_string(publication.paper_nr))
            new_path = new_dir + '/' + publication.doi_label.replace('.', '_') + '.pdf'
            os.makedirs(new_dir)
            os.rename(initial_path, new_path)
            publication.pdf_file.name = new_path
            publication.save()
            # Mark the submission as having been published:
            publication.accepted_submission.published_as = publication
            publication.accepted_submission.status = 'published'
            publication.accepted_submission.save()
            # TODO: Create a Commentary Page
            # Email authors
            JournalUtils.load({'publication': publication})
            JournalUtils.send_authors_paper_published_email()
            ack_header = 'The publication has been validated.'
            context = {'ack_header': ack_header,}
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was invalid.'
            context = {'publication': publication,
                       'validate_publication_form': validate_publication_form,
                       'errormessage': errormessage}
            return render(request, 'journals/validate_publication.html', context)
    else:
        validate_publication_form = ValidatePublicationForm()
    context = {'validate_publication_form': validate_publication_form}
    return render(request, 'journals/validate_publication.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_citation_list_metadata(request, doi_string):
    """
    Called by an Editorial Administrator.
    This populates the citation_list dictionary entry 
    in the metadata field in a Publication instance.
    """
    publication = get_object_or_404(Publication, doi_string=doi_string)
    if request.method == 'POST':
        bibitems_form = CitationListBibitemsForm(request.POST, request.FILES)
        if bibitems_form.is_valid():
            publication.metadata['citation_list'] = []
            entries_list = bibitems_form.cleaned_data['latex_bibitems'].split('\doi{')
            nentries = 1
            for entry in entries_list[1:]: # drop first bit before first \doi{ 
                publication.metadata['citation_list'].append(
                    {'key': 'ref' + str(nentries),
                     'doi': entry.partition('}')[0],}
                )
                nentries += 1
            publication.save()
    bibitems_form = CitationListBibitemsForm()
    context = {'publication': publication,
               'bibitems_form': bibitems_form,
    }
    if request.method == 'POST':
        context['citation_list'] = publication.metadata['citation_list']
    return render(request, 'journals/create_citation_list_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_funding_info_metadata(request, doi_string):
    """
    Called by an Editorial Administrator.
    This populates the funding_info dictionary entry 
    in the metadata field in a Publication instance.
    """
    publication = get_object_or_404(Publication, doi_string=doi_string)
    if request.method == 'POST':
        funding_info_form = FundingInfoForm(request.POST)
        if funding_info_form.is_valid():
            publication.metadata['funding_statement'] = funding_info_form.cleaned_data['funding_statement']
            publication.save()

    initial = {'funding_statement': '',}
    funding_statement = ''
    try:
        initial['funding_statement'] = publication.metadata['funding_statement']
        funding_statement = initial['funding_statement']
    except KeyError:
        pass
    context = {'publication': publication,
               'funding_info_form': FundingInfoForm(initial=initial),
               'funding_statement': funding_statement,}

    return render(request, 'journals/create_funding_info_metadata.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def create_metadata_xml(request, doi_string):
    """ 
    To be called by an EdAdmin after the citation_list,
    funding_info entries have been filled.
    Populates the metadata_xml field of a Publication instance.
    The contents can then be sent to Crossref for registration.
    """
    publication = get_object_or_404(Publication, doi_string=doi_string)

    if request.method == 'POST':
        create_metadata_xml_form = CreateMetadataXMLForm(request.POST)
        if create_metadata_xml_form.is_valid():
            publication.metadata_xml = create_metadata_xml_form.cleaned_data['metadata_xml']
            publication.save()
            return redirect(reverse('scipost:publication_detail', 
                                    kwargs={'doi_string': publication.doi_string,}))

    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode('utf8')
    idsalt = publication.title[:10]
    idsalt = idsalt.encode('utf8')
    doi_batch_id = hashlib.sha1(salt+idsalt).hexdigest()

    #publication.metadata_xml = (
    initial = {'metadata_xml': ''}
    initial['metadata_xml'] += (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<doi_batch version="4.3.7" xmlns="http://www.crossref.org/schema/4.3.7" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.crossref.org/schema/4.3.7 '
        'http://www.crossref.org/shema/deposit/crossref4.3.7.xsd">\n'
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
        '<full_title>' + publication.in_issue.in_volume.in_journal.name + '</full_title>\n'
        '<abbrev_title>' 
        + journal_name_abbrev_citation(publication.in_issue.in_volume.in_journal.name) +
        '</abbrev_title>\n'
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
            #publication.metadata_xml += (
            initial['metadata_xml'] += (
                '<person_name sequence=\'first\' contributor_role=\'author\'> '
                '<given_name>' + author.user.first_name + '</given_name> '
                '<surname>' + author.user.last_name + '</surname> '
                '</person_name>\n'
            )
        else:
            #publication.metadata_xml += (
            initial['metadata_xml'] += (
                '<person_name sequence=\'additional\' contributor_role=\'author\'> '
                '<given_name>' + author.user.first_name + '</given_name> '
                '<surname>' + author.user.last_name + '</surname> '
                '</person_name>\n'
            )
        if author.orcid_id:
            #publication.metadata_xml += '<ORCID>' + author.orcid_id + '</ORCID>\n'
            initial['metadata_xml'] += '<ORCID>' + author.orcid_id + '</ORCID>\n'

            #publication.metadata_xml += '</contributors>\n'
            initial['metadata_xml'] += '</contributors>\n'

    #publication.metadata_xml += (
    initial['metadata_xml'] += (
        '<publication_date media_type=\'online\'>\n'
        '<month>' + publication.publication_date.strftime('%m') + '</month>'
        '<day>' + publication.publication_date.strftime('%d') + '</day>'
        '<year>' + publication.publication_date.strftime('%Y') + '</year>'
        '</publication_date>\n'
        '<publisher_item><item_number item_number_type="article_number">'
        + paper_nr_string(publication.paper_nr) + 
        '</item_number></publisher_item>/n'
        '<doi_data>\n'
        '<doi>' + publication.doi_string + '</doi>'
        '<resource>https://scipost.org/' + publication.doi_string + '</resource>'
        '</doi_data>\n'
    )
    if publication.metadata['citation_list']:
        #publication.metadata_xml += '<citation_list>\n'
        initial['metadata_xml'] += '<citation_list>\n'
        for ref in publication.metadata['citation_list']:
            #publication.metadata_xml += (
            initial['metadata_xml'] += (
                '<citation key="' + ref['key'] + '">'
                '<doi>' + ref['doi'] + '</doi>'
                '</citation>\n'
            )
        #publication.metadata_xml += '</citation_list>\n'
        initial['metadata_xml'] += '</citation_list>\n'

    #publication.metadata_xml += (
    initial['metadata_xml'] += (
        '</journal_article>\n'
        '</journal>\n'
    )
    #publication.metadata_xml += '</body>\n</doi_batch>'
    initial['metadata_xml'] += '</body>\n</doi_batch>'
    publication.save()
    #else:
    #   errormessage = 'The form was invalidly filled.'

    context = {'publication': publication,
               'create_metadata_xml_form': CreateMetadataXMLForm(initial=initial),
               }
    return render(request, 'journals/create_metadata_xml.html', context)


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
@transaction.atomic
def test_metadata_xml_deposit(request, doi_string):
    """
    Prior to the actual Crossref metadata deposit,
    test the metadata_xml using the Crossref test server.
    Makes use of the python requests module.
    """
    publication = get_object_or_404 (Publication, doi_string=doi_string)
    url = 'https://test.crossref.org/servlet/deposit'
    #headers = {'Content-type': 'multipart/form-data'}
    params = {'operation': 'doMDUpload',
              'login_id': settings.CROSSREF_LOGIN_ID,
              'login_passwd': settings.CROSSREF_LOGIN_PASSWORD,
          }
    #auth = (settings.CROSSREF_LOGIN_ID, settings.CROSSREF_LOGIN_PASSWORD)
    files = {'fname': ('metadata.xml', publication.metadata_xml, 'multipart/form-data', {}),}
    #files = {'file': (publication.metadata_xml),}
    r = requests.post(url, 
                      #auth=auth, 
                      #headers=headers, 
                      params=params, 
                      files=files)
    response_headers = r.headers
    context = {'response_headers': response_headers,}
    return render(requests, 'journals/text_metadata_xml_deposit.html', context)



###########
# Viewing #
###########

def publication_detail(request, doi_string):
    publication = get_object_or_404 (Publication, doi_string=doi_string)
    context = {'publication': publication,}
    return render(request, 'journals/publication_detail.html', context)


def publication_pdf(request, doi_string):
    publication = get_object_or_404 (Publication, doi_string=doi_string)
    pdf = File(publication.pdf_file)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = ('filename=' 
                                       + publication.doi_label.replace('.', '_') + '.pdf')
    return response

def publication_detail_form_doi_label(request, doi_label):
    publication = get_object_or_404 (Publication, doi_label=doi_label)
    context = {'publication': publication,}
    return render(request, 'journals/publication_detail.html', context)


def publication_pdf_from_doi_label(request, doi_label):
    publication = get_object_or_404 (Publication, doi_label=doi_label)
    pdf = File(publication.pdf_file)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = ('filename=' 
                                       + publication.doi_label.replace('.', '_') + '.pdf')
    return response
