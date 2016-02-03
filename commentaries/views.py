import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
#from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from comments.models import Comment, AuthorReply
from comments.forms import CommentForm
from scipost.forms import TITLE_CHOICES, AuthenticationForm
from ratings.forms import CommentRatingForm, AuthorReplyRatingForm, CommentaryRatingForm

title_dict = dict(TITLE_CHOICES) # Convert titles for use in emails

################
# Commentaries
################


def howto(request):
    return render(request, 'commentaries/howto.html')

def request_commentary(request):
    # commentary pages can only be requested by registered contributors:
    if request.user.is_authenticated():
        # If POST, process the form data
        if request.method == 'POST':
            form = RequestCommentaryForm(request.POST)
            if form.is_valid():
                contributor = Contributor.objects.get(user=request.user)
                commentary = Commentary (
                    requested_by = contributor,
                    type = form.cleaned_data['type'],
                    discipline = form.cleaned_data['discipline'],
                    pub_title = form.cleaned_data['pub_title'],
                    arxiv_link = form.cleaned_data['arxiv_link'],
                    pub_DOI_link = form.cleaned_data['pub_DOI_link'],
                    author_list = form.cleaned_data['author_list'],
                    pub_date = form.cleaned_data['pub_date'],
                    pub_abstract = form.cleaned_data['pub_abstract'],
                    latest_activity = timezone.now(),
                    )
                commentary.save()
                return HttpResponseRedirect('request_commentary_ack')
        else:
            form = RequestCommentaryForm()
        return render(request, 'commentaries/request_commentary.html', {'form': form})
    else: # user is not authenticated:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


def request_commentary_ack(request):
    return render(request, 'commentaries/request_commentary_ack.html')


def vet_commentary_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    commentary_to_vet = Commentary.objects.filter(vetted=False).first() # only handle one at a time
    #if commentary_to_vet is not None:
    form = VetCommentaryForm()
    context = {'contributor': contributor, 'commentary_to_vet': commentary_to_vet, 'form': form }
    return render(request, 'commentaries/vet_commentary_requests.html', context)


def vet_commentary_request_ack(request, commentary_id):
    if request.method == 'POST':
        form = VetCommentaryForm(request.POST)
        commentary = Commentary.objects.get(pk=commentary_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the commentary as is
                commentary.vetted = True
                commentary.vetted_by = Contributor.objects.get(user=request.user)
                commentary.save()
                email_text = 'Dear ' + title_dict[commentary.requested_by.title] + ' ' + commentary.requested_by.user.last_name + ', \n\nThe Commentary Page you have requested, concerning publication with title ' + commentary.pub_title + ' by ' + commentary.author_list + ', has been activated. You are now welcome to submit your comments.' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text, 'commentaries@scipost.org', [commentary.requested_by.user.email, 'commentaries@scipost.org'], reply_to=['commentaries@scipost.org'])
                emailmessage.send(fail_silently=False)                
            elif form.cleaned_data['action_option'] == '0':
                # re-edit the form starting from the data provided
                form2 = RequestCommentaryForm(initial={'pub_title': commentary.pub_title, 'arxiv_link': commentary.arxiv_link, 'pub_DOI_link': commentary.pub_DOI_link, 'author_list': commentary.author_list, 'pub_date': commentary.pub_date, 'pub_abstract': commentary.pub_abstract})
                commentary.delete()
                email_text = 'Dear ' + title_dict[commentary.requested_by.title] + ' ' + commentary.requested_by.user.last_name + ', \n\nThe Commentary Page you have requested, concerning publication with title ' + commentary.pub_title + ' by ' + commentary.author_list + ', has been activated (with slight modifications to your submitted details). You are now welcome to submit your comments.' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text, 'commentaries@scipost.org', [commentary.requested_by.user.email, 'commentaries@scipost.org'], reply_to=['commentaries@scipost.org'])
                emailmessage.send(fail_silently=False)                
                context = {'form': form2 }
                return render(request, 'commentaries/request_commentary.html', context)
            elif form.cleaned_data['action_option'] == '2':
                # the commentary request is simply rejected
                email_text = 'Dear ' + title_dict[commentary.requested_by.title] + ' ' + commentary.requested_by.user.last_name + ', \n\nThe Commentary Page you have requested, concerning publication with title ' + commentary.pub_title + ' by ' + commentary.author_list + ', has not been activated for the following reason: ' + form.cleaned_data['refusal_reason'] + '.\n\nThank you for your interest, \nThe SciPost Team.'
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost Commentary Page activated', email_text, 'commentaries@scipost.org', [commentary.requested_by.user.email, 'commentaries@scipost.org'], reply_to=['comentaries@scipost.org'])
                emailmessage.send(fail_silently=False)                
                commentary.delete()

#    context = {'option': form.cleaned_data['action_option'], 'reason': form.cleaned_data['refusal_reason'] }
    context = {'commentary_id': commentary_id }
    return render(request, 'commentaries/vet_commentary_request_ack.html', context)


def commentaries(request):
    if request.method == 'POST':
        form = CommentarySearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            commentary_search_list = Commentary.objects.filter(
                pub_title__icontains=form.cleaned_data['pub_title_keyword'],
                author_list__icontains=form.cleaned_data['pub_author'],
                pub_abstract__icontains=form.cleaned_data['pub_abstract_keyword'],
                vetted=True,
                )
            commentary_search_list.order_by('-pub_date')
        else:
            commentary_search_list = [] 
           
    else:
        form = CommentarySearchForm()
        commentary_search_list = []

    commentary_recent_list = Commentary.objects.filter(vetted=True, latest_activity__gte=timezone.now() + datetime.timedelta(days=-7))
    context = {'form': form, 'commentary_search_list': commentary_search_list, 'commentary_recent_list': commentary_recent_list }
    return render(request, 'commentaries/commentaries.html', context)


def browse(request, discipline, nrweeksback):
    if request.method == 'POST':
        form = CommentarySearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            commentary_search_list = Commentary.objects.filter(
                pub_title__icontains=form.cleaned_data['pub_title_keyword'],
                author_list__icontains=form.cleaned_data['pub_author'],
                pub_abstract__icontains=form.cleaned_data['pub_abstract_keyword'],
                vetted=True,
                )
            commentary_search_list.order_by('-pub_date')
        else:
            commentary_search_list = [] 
        context = {'form': form, 'commentary_search_list': commentary_search_list }
        return HttpResponseRedirect(request, 'commentaries/commentaries.html', context)
    else:
        form = CommentarySearchForm()
    commentary_browse_list = Commentary.objects.filter(vetted=True, discipline=discipline, latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback)))
    context = {'form': form, 'discipline': discipline, 'nrweeksback': nrweeksback, 'commentary_browse_list': commentary_browse_list }
    #return render(request, 'commentaries/browse.html', context)
    #return HttpResponseRedirect(request, 'commentaries/commentaries.html', context)
    return render(request, 'commentaries/commentaries.html', context)


def commentary_detail(request, commentary_id):
    commentary = get_object_or_404(Commentary, pk=commentary_id)
    comments = commentary.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newcomment = Comment (
                commentary = commentary,
                in_reply_to = None,
                author = author,
                is_rem = form.cleaned_data['is_rem'],
                is_que = form.cleaned_data['is_que'],
                is_ans = form.cleaned_data['is_ans'],
                is_obj = form.cleaned_data['is_obj'],
                is_rep = form.cleaned_data['is_rep'],
                is_val = form.cleaned_data['is_val'],
                is_lit = form.cleaned_data['is_lit'],
                is_sug = form.cleaned_data['is_sug'],
                comment_text = form.cleaned_data['comment_text'],
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
            author.nr_comments = Comment.objects.filter(author=author).count()
            author.save()
            request.session['commentary_id'] = commentary_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    comment_rating_form = CommentRatingForm()
    authorreply_rating_form = AuthorReplyRatingForm()
    commentary_rating_form = CommentaryRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(commentary=commentary)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'commentary': commentary, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'author_replies': author_replies, 'form': form, 'commentary_rating_form': commentary_rating_form, 'comment_rating_form': comment_rating_form, 'authorreply_rating_form': authorreply_rating_form }
    return render(request, 'commentaries/commentary_detail.html', context)
