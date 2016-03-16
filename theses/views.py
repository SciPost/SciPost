import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
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
from ratings.forms import CommentRatingForm, AuthorReplyRatingForm, CommentaryRatingForm, ThesisLinkRatingForm

title_dict = dict(TITLE_CHOICES) # Convert titles for use in emails

################
# Theses
################


def request_thesislink(request):
    if request.user.is_authenticated():
        # If POST, process the form data
        if request.method == 'POST':
            form = RequestThesisLinkForm(request.POST)
            if form.is_valid():
                contributor = Contributor.objects.get(user=request.user)
                thesislink = ThesisLink (
                    requested_by = contributor,
                    type = form.cleaned_data['type'],
                    discipline = form.cleaned_data['discipline'],
                    domain = form.cleaned_data['domain'],
                    specialization = form.cleaned_data['specialization'],
                    title = form.cleaned_data['title'],
                    author = form.cleaned_data['author'],
                    supervisor = form.cleaned_data['supervisor'],
                    institution = form.cleaned_data['institution'],
                    defense_date = form.cleaned_data['defense_date'],
                    pub_link = form.cleaned_data['pub_link'],
                    abstract = form.cleaned_data['abstract'],
                    latest_activity = timezone.now(),
                    )
                thesislink.save()
                return HttpResponseRedirect('request_thesislink_ack')
        else:
            form = RequestThesisLinkForm()
        return render(request, 'theses/request_thesislink.html', {'form': form})
    else: # user is not authenticated:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})


def vet_thesislink_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    thesislink_to_vet = ThesisLink.objects.filter(vetted=False).first() # only handle one at a time
    form = VetThesisLinkForm()
    context = {'contributor': contributor, 'thesislink_to_vet': thesislink_to_vet, 'form': form }
    return render(request, 'theses/vet_thesislink_requests.html', context)


def vet_thesislink_request_ack(request, thesislink_id):
    if request.method == 'POST':
        form = VetThesisLinkForm(request.POST)
        thesislink = ThesisLink.objects.get(pk=thesislink_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                thesislink.vetted = True
                thesislink.vetted_by = Contributor.objects.get(user=request.user)
                thesislink.save()
                email_text = 'Dear ' + title_dict[thesislink.requested_by.title] + ' ' + thesislink.requested_by.user.last_name + ', \n\nThe Thesis Link you have requested, concerning thesis with title ' + thesislink.title + ' by ' + thesislink.author + ', has been activated.' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Thesis Link activated', email_text, 'theses@scipost.org', [thesislink.requested_by.user.email, 'theses@scipost.org'], reply_to=['theses@scipost.org'])
                emailmessage.send(fail_silently=False)                
            elif form.cleaned_data['action_option'] == '0':
                # re-edit the form starting from the data provided
                form2 = RequestThesisLinkForm(initial={'title': thesislink.pub_title, 'pub_ink': thesislink.pub_link, 'author': thesislink.author, 'institution': thesislink.institution, 'defense_date': thesislink.defense_date, 'abstract': thesislink.abstract})
                thesislink.delete()
                email_text = 'Dear ' + title_dict[thesislink.requested_by.title] + ' ' + thesislink.requested_by.user.last_name + ', \n\nThe Thesis Link you have requested, concerning thesis with title ' + thesislink.title + ' by ' + thesislink.author_list + ', has been activated (with slight modifications to your submitted details).' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Thesis Link activated', email_text, 'theses@scipost.org', [thesislink.requested_by.user.email, 'theses@scipost.org'], reply_to=['theses@scipost.org'])
                # Don't send email yet... only when option 1 has succeeded!
                #emailmessage.send(fail_silently=False)                
                context = {'form': form2 }
                return render(request, 'theses/request_thesislink.html', context)
            elif form.cleaned_data['action_option'] == '2':
                email_text = 'Dear ' + title_dict[thesislink.requested_by.title] + ' ' + thesislink.requested_by.user.last_name + ', \n\nThe Thesis Link you have requested, concerning thesis with title ' + thesislink.title + ' by ' + thesislink.author + ', has not been activated for the following reason: ' + form.cleaned_data['refusal_reason'] + '.\n\nThank you for your interest, \nThe SciPost Team.'
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost Thesis Link', email_text, 'theses@scipost.org', [thesislink.requested_by.user.email, 'theses@scipost.org'], reply_to=['theses@scipost.org'])
                emailmessage.send(fail_silently=False)                
                thesislink.delete()

    context = {'thesislink_id': thesislink_id }
    return render(request, 'theses/vet_thesislink_request_ack.html', context)


def theses(request):
    if request.method == 'POST':
        form = ThesisLinkSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            thesislink_search_list = ThesisLink.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                supervisor__icontains=form.cleaned_data['supervisor'],
                vetted=True,
                )
            thesislink_search_list.order_by('-pub_date')
        else:
            thesislink_search_list = [] 
           
    else:
        form = ThesisLinkSearchForm()
        thesislink_search_list = []

    thesislink_recent_list = ThesisLink.objects.filter(vetted=True, latest_activity__gte=timezone.now() + datetime.timedelta(days=-7))
    context = {'form': form, 'thesislink_search_list': thesislink_search_list, 'thesislink_recent_list': thesislink_recent_list }
    return render(request, 'theses/theses.html', context)


def browse(request, discipline, nrweeksback):
    if request.method == 'POST':
        form = ThesisLinkSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            thesislink_search_list = ThesisLink.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                supervisor__icontains=form.cleaned_data['supervisor'],
                vetted=True,
                )
            thesislink_search_list.order_by('-pub_date')
        else:
            thesislink_search_list = [] 
        context = {'form': form, 'thesislink_search_list': thesislink_search_list }
        return HttpResponseRedirect(request, 'theses/theses.html', context)
    else:
        form = ThesisLinkSearchForm()
    thesislink_browse_list = ThesisLink.objects.filter(vetted=True, discipline=discipline, latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback)))
    context = {'form': form, 'discipline': discipline, 'nrweeksback': nrweeksback, 'thesislink_browse_list': thesislink_browse_list }
    return render(request, 'theses/theses.html', context)


def thesis_detail(request, thesislink_id):
    thesislink = get_object_or_404(ThesisLink, pk=thesislink_id)
    comments = thesislink.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newcomment = Comment (
                thesislink = thesislink,
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
            request.session['thesislink_id'] = thesislink_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    comment_rating_form = CommentRatingForm()
    authorreply_rating_form = AuthorReplyRatingForm()
    thesislink_rating_form = ThesisLinkRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(thesislink=thesislink)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'thesislink': thesislink, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'author_replies': author_replies, 'form': form, 'thesislink_rating_form': thesislink_rating_form, 'comment_rating_form': comment_rating_form, 'authorreply_rating_form': authorreply_rating_form }
    return render(request, 'theses/thesis_detail.html', context)
