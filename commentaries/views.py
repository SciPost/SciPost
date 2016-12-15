import datetime
import feedparser
import re
import requests

from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect

from .models import Commentary
from .forms import RequestCommentaryForm, DOIToQueryForm, IdentifierToQueryForm
from .forms import VetCommentaryForm, CommentarySearchForm, commentary_refusal_dict

from comments.models import Comment
from comments.forms import CommentForm
from scipost.models import Contributor
from scipost.models import title_dict
from scipost.forms import AuthenticationForm


################
# Commentaries
################


@login_required
@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def request_commentary(request):
    form = RequestCommentaryForm(request.POST or None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            commentary = form.save(commit=False)
            commentary.parse_links_into_urls()
            commentary.save()

            context = {'ack_header': 'Thank you for your request for a Commentary Page',
                       'ack_message': 'Your request will soon be handled by an Editor. ',
                       'followup_message': 'Return to your ',
                       'followup_link': reverse('scipost:personal_page'),
                       'followup_link_label': 'personal page'}
            return render(request, 'scipost/acknowledgement.html', context)

        else:
            doiform = DOIToQueryForm()
            existing_commentary = form.get_existing_commentary()
            identifierform = IdentifierToQueryForm()
            context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,
                       'errormessage': form.errors,
                       'existing_commentary': existing_commentary}
            return render(request, 'commentaries/request_commentary.html', context)

    doiform = DOIToQueryForm()
    identifierform = IdentifierToQueryForm()
    context = {'form': form, 'doiform': doiform, 'identifierform': identifierform}
    return render(request, 'commentaries/request_commentary.html', context)

@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def prefill_using_DOI(request):
    """ Probes CrossRef API with the DOI, to pre-fill the form. """
    if request.method == "POST":
        doiform = DOIToQueryForm(request.POST)
        if doiform.is_valid():
            # Check if given doi is of expected form:
            doipattern = re.compile("^10.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+")
            errormessage = ''
            existing_commentary = None
            if not doipattern.match(doiform.cleaned_data['doi']):
                errormessage = 'The DOI you entered is improperly formatted.'
            elif Commentary.objects.filter(pub_DOI=doiform.cleaned_data['doi']).exists():
                errormessage = 'There already exists a Commentary Page on this publication, see'
                existing_commentary = get_object_or_404(Commentary, pub_DOI=doiform.cleaned_data['doi'])
            if errormessage:
                form = RequestCommentaryForm()
                identifierform = IdentifierToQueryForm()
                context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,
                           'errormessage': errormessage,
                           'existing_commentary': existing_commentary}
                return render(request, 'commentaries/request_commentary.html', context)

            # Otherwise we query Crossref for the information:
            try:
                queryurl = 'http://api.crossref.org/works/%s' % doiform.cleaned_data['doi']
                doiquery = requests.get(queryurl)
                doiqueryJSON = doiquery.json()
                metadata = doiqueryJSON
                pub_title = doiqueryJSON['message']['title'][0]
                authorlist = (doiqueryJSON['message']['author'][0]['given'] + ' ' +
                              doiqueryJSON['message']['author'][0]['family'])
                for author in doiqueryJSON['message']['author'][1:]:
                    authorlist += ', ' + author['given'] + ' ' + author['family']
                journal = doiqueryJSON['message']['container-title'][0]

                try:
                    volume = doiqueryJSON['message']['volume']
                except KeyError:
                    volume = ''

                pages = ''
                try:
                    pages = doiqueryJSON['message']['article-number'] # for Phys Rev
                except KeyError:
                    pass
                try:
                    pages = doiqueryJSON['message']['page']
                except KeyError:
                    pass

                pub_date = ''
                try:
                    pub_date = (str(doiqueryJSON['message']['issued']['date-parts'][0][0]) + '-' +
                                str(doiqueryJSON['message']['issued']['date-parts'][0][1]))
                    try:
                        pub_date += '-' + str(doiqueryJSON['message']['issued']['date-parts'][0][2])
                    except (IndexError, KeyError):
                        pass
                except (IndexError, KeyError):
                    pass
                pub_DOI = doiform.cleaned_data['doi']
                form = RequestCommentaryForm(
                    initial={'type': 'published', 'metadata': metadata,
                             'pub_title': pub_title, 'author_list': authorlist,
                             'journal': journal, 'volume': volume,
                             'pages': pages, 'pub_date': pub_date,
                             'pub_DOI': pub_DOI})
                identifierform = IdentifierToQueryForm()
                context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,}
                context['title'] = pub_title
                return render(request, 'commentaries/request_commentary.html', context)
            except (IndexError, KeyError, ValueError):
                pass
        else:
            pass
    return redirect(reverse('commentaries:request_commentary'))

@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def prefill_using_identifier(request):
    """ Probes arXiv with the identifier, to pre-fill the form. """
    if request.method == "POST":
        identifierform = IdentifierToQueryForm(request.POST)
        if identifierform.is_valid():
            # Check if given identifier is of expected form:
            # we allow 1 or 2 digits for version
            identifierpattern_new = re.compile("^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$")
            identifierpattern_old = re.compile("^[-.a-z]+/[0-9]{7,}v[0-9]{1,2}$")
            errormessage = ''
            existing_commentary = None
            if not (identifierpattern_new.match(identifierform.cleaned_data['identifier']) or
                    identifierpattern_old.match(identifierform.cleaned_data['identifier'])):
                errormessage = ('The identifier you entered is improperly formatted '
                                '(did you forget the version number?).')
            elif (Commentary.objects
                  .filter(arxiv_identifier=identifierform.cleaned_data['identifier']).exists()):
                errormessage = 'There already exists a Commentary Page on this preprint, see'
                existing_commentary = get_object_or_404(
                    Commentary, arxiv_identifier=identifierform.cleaned_data['identifier'])
            if errormessage:
                form = RequestCommentaryForm()
                doiform = DOIToQueryForm()
                context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,
                           'errormessage': errormessage,
                           'existing_commentary': existing_commentary}
                return render(request, 'commentaries/request_commentary.html', context)
            # Otherwise we query arXiv for the information:
            try:
                queryurl = ('http://export.arxiv.org/api/query?id_list=%s'
                            % identifierform.cleaned_data['identifier'])
                arxivquery = feedparser.parse(queryurl)

                # If paper has been published, should comment on published version
                try:
                    arxiv_journal_ref = arxivquery['entries'][0]['arxiv_journal_ref']
                    errormessage = ('This paper has been published as ' + arxiv_journal_ref
                                    + '. Please comment on the published version.')
                except (IndexError, KeyError):
                    pass
                try:
                    arxiv_doi = arxivquery['entries'][0]['arxiv_doi']
                    errormessage = ('This paper has been published under DOI ' + arxiv_DOI
                                    + '. Please comment on the published version.')
                except (IndexError, KeyError):
                    pass

                if errormessage:
                    form = RequestCommentaryForm()
                    doiform = DOIToQueryForm()
                    context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,
                               'errormessage': errormessage,
                               'existing_commentary': existing_commentary}
                    return render(request, 'commentaries/request_commentary.html', context)

                # otherwise prefill the form:
                metadata = arxivquery
                pub_title = arxivquery['entries'][0]['title']
                authorlist = arxivquery['entries'][0]['authors'][0]['name']
                for author in arxivquery['entries'][0]['authors'][1:]:
                    authorlist += ', ' + author['name']
                arxiv_link = arxivquery['entries'][0]['id']
                abstract = arxivquery['entries'][0]['summary']
                form = RequestCommentaryForm(
                    initial={'type': 'preprint', 'metadata': metadata,
                             'pub_title': pub_title, 'author_list': authorlist,
                             'arxiv_identifier': identifierform.cleaned_data['identifier'],
                             'arxiv_link': arxiv_link, 'pub_abstract': abstract})
                doiform = DOIToQueryForm()
                context = {'form': form, 'doiform': doiform, 'identifierform': identifierform}
                context['title'] = pub_title
                return render(request, 'commentaries/request_commentary.html', context)
            except (IndexError, KeyError, ValueError): # something went wrong with processing the arXiv data
                errormessage = 'An error occurred while processing the arXiv data. Are you sure this identifier exists?'
                form = RequestCommentaryForm()
                doiform = DOIToQueryForm()
                context = {'form': form, 'doiform': doiform, 'identifierform': identifierform,
                           'errormessage': errormessage,
                           'existing_commentary': existing_commentary}
                return render(request, 'commentaries/request_commentary.html', context)
        else:
            pass
    return redirect(reverse('commentaries:request_commentary'))


@permission_required('scipost.can_vet_commentary_requests', raise_exception=True)
def vet_commentary_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    commentary_to_vet = Commentary.objects.awaiting_vetting().first() # only handle one at a time
    form = VetCommentaryForm()
    context = {'contributor': contributor, 'commentary_to_vet': commentary_to_vet, 'form': form }
    return render(request, 'commentaries/vet_commentary_requests.html', context)

@permission_required('scipost.can_vet_commentary_requests', raise_exception=True)
def vet_commentary_request_ack(request, commentary_id):
    if request.method == 'POST':
        form = VetCommentaryForm(request.POST)
        commentary = Commentary.objects.get(pk=commentary_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the commentary as is
                commentary.vetted = True
                commentary.vetted_by = Contributor.objects.get(user=request.user)
                commentary.latest_activity = timezone.now()
                commentary.save()
                email_text = ('Dear ' + title_dict[commentary.requested_by.title] + ' '
                              + commentary.requested_by.user.last_name
                              + ', \n\nThe Commentary Page you have requested, '
                              'concerning publication with title '
                              + commentary.pub_title + ' by ' + commentary.author_list
                              + ', has been activated at https://scipost.org/commentary/'
                              + str(commentary.arxiv_or_DOI_string)
                              + '. You are now welcome to submit your comments.'
                              '\n\nThank you for your contribution, \nThe SciPost Team.')
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text,
                                            'SciPost commentaries <commentaries@scipost.org>',
                                            [commentary.requested_by.user.email],
                                            ['commentaries@scipost.org'],
                                            reply_to=['commentaries@scipost.org'])
                emailmessage.send(fail_silently=False)
            elif form.cleaned_data['action_option'] == '0':
                # re-edit the form starting from the data provided
                form2 = RequestCommentaryForm(initial={'pub_title': commentary.pub_title,
                                                       'arxiv_link': commentary.arxiv_link,
                                                       'pub_DOI_link': commentary.pub_DOI_link,
                                                       'author_list': commentary.author_list,
                                                       'pub_date': commentary.pub_date,
                                                       'pub_abstract': commentary.pub_abstract})
                commentary.delete()
                email_text = ('Dear ' + title_dict[commentary.requested_by.title] + ' '
                              + commentary.requested_by.user.last_name
                              + ', \n\nThe Commentary Page you have requested, '
                              'concerning publication with title ' + commentary.pub_title
                              + ' by ' + commentary.author_list
                              + ', has been activated (with slight modifications to your submitted details).'
                              ' You are now welcome to submit your comments.'
                              '\n\nThank you for your contribution, \nThe SciPost Team.')
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text,
                                            'SciPost commentaries <commentaries@scipost.org>',
                                            [commentary.requested_by.user.email],
                                            ['commentaries@scipost.org'],
                                            reply_to=['commentaries@scipost.org'])
                emailmessage.send(fail_silently=False)
                context = {'form': form2 }
                return render(request, 'commentaries/request_commentary.html', context)
            elif form.cleaned_data['action_option'] == '2':
                # the commentary request is simply rejected
                email_text = ('Dear ' + title_dict[commentary.requested_by.title] + ' '
                              + commentary.requested_by.user.last_name
                              + ', \n\nThe Commentary Page you have requested, '
                              'concerning publication with title '
                              + commentary.pub_title + ' by ' + commentary.author_list
                              + ', has not been activated for the following reason: '
                              + commentary_refusal_dict[int(form.cleaned_data['refusal_reason'])]
                              + '.\n\nThank you for your interest, \nThe SciPost Team.')
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text,
                                            'SciPost commentaries <commentaries@scipost.org>',
                                            [commentary.requested_by.user.email],
                                            ['commentaries@scipost.org'],
                                            reply_to=['comentaries@scipost.org'])
                emailmessage.send(fail_silently=False)
                commentary.delete()

    context = {'ack_header': 'SciPost Commentary request vetted.',
               'followup_message': 'Return to the ',
               'followup_link': reverse('commentaries:vet_commentary_requests'),
               'followup_link_label': 'Commentary requests page'}
    return render(request, 'scipost/acknowledgement.html', context)

def commentaries(request):
    """List and search all commentaries"""
    form = CommentarySearchForm(request.POST or None)
    if form.is_valid() and form.has_changed():
        commentary_search_list = form.search_results()
    else:
        commentary_search_list = []

    comment_recent_list = Comment.objects.filter(status='1').order_by('-date_submitted')[:10]
    commentary_recent_list = Commentary.objects.vetted().order_by('-latest_activity')[:10]
    context = {
        'form': form, 'commentary_search_list': commentary_search_list,
        'comment_recent_list': comment_recent_list,
        'commentary_recent_list': commentary_recent_list}
    return render(request, 'commentaries/commentaries.html', context)

def browse(request, discipline, nrweeksback):
    """List all commentaries for discipline and period"""
    commentary_browse_list = Commentary.objects.vetted(
        discipline=discipline,
        latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback)))
    context = {
        'form': CommentarySearchForm(),
        'discipline': discipline, 'nrweeksback': nrweeksback,
        'commentary_browse_list': commentary_browse_list}
    return render(request, 'commentaries/commentaries.html', context)

def commentary_detail(request, arxiv_or_DOI_string):
    commentary = get_object_or_404(Commentary, arxiv_or_DOI_string=arxiv_or_DOI_string)
    comments = commentary.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newcomment = Comment(commentary=commentary, author=author,
                is_rem=form.cleaned_data['is_rem'],
                is_que=form.cleaned_data['is_que'],
                is_ans=form.cleaned_data['is_ans'],
                is_obj=form.cleaned_data['is_obj'],
                is_rep=form.cleaned_data['is_rep'],
                is_val=form.cleaned_data['is_val'],
                is_lit=form.cleaned_data['is_lit'],
                is_sug=form.cleaned_data['is_sug'],
                comment_text=form.cleaned_data['comment_text'],
                remarks_for_editors=form.cleaned_data['remarks_for_editors'],
                date_submitted=timezone.now(),
                )
            newcomment.save()
            author.nr_comments = Comment.objects.filter(author=author).count()
            author.save()
            context = {'ack_header': 'Thank you for contributing a Comment.',
                       'ack_message': 'It will soon be vetted by an Editor.',
                       'followup_message': 'Back to the ',
                       'followup_link': reverse(
                           'commentaries:commentary',
                           kwargs={'arxiv_or_DOI_string': newcomment.commentary.arxiv_or_DOI_string}
                       ),
                       'followup_link_label': ' Commentary page you came from'
                   }
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = CommentForm()
    try:
        author_replies = Comment.objects.filter(commentary=commentary,
                                                is_author_reply=True,
                                                status__gte=1)
    except Comment.DoesNotExist:
        author_replies = ()
    context = {'commentary': commentary,
               'comments': comments.filter(status__gte=1).order_by('-date_submitted'),
               'author_replies': author_replies, 'form': form}
    return render(request, 'commentaries/commentary_detail.html', context)
