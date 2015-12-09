import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from comments.models import Comment, AuthorReply
from comments.forms import CommentForm
from ratings.forms import CommentRatingForm, CommentaryRatingForm

################
# Commentaries
################

@csrf_protect
def request_commentary(request):
    # commentary pages can only be requested by registered contributors:
    if request.user.is_authenticated():
        # If POST, process the form data
        if request.method == 'POST':
            form = RequestCommentaryForm(request.POST)
            if form.is_valid():
                contributor = Contributor.objects.get(user=request.user)
                commentary = Commentary (
                    type = form.cleaned_data['type'],
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
        return render(request, 'contributors/login.html')

def request_commentary_ack(request):
    return render(request, 'commentaries/request_commentary_ack.html')


@csrf_protect
def vet_commentary_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    commentary_requests_to_vet = Commentary.objects.filter(vetted=False)
    form = VetCommentaryForm()
    context = {'contributor': contributor, 'commentary_requests_to_vet': commentary_requests_to_vet, 'form': form }
    return render(request, 'commentaries/vet_commentary_requests.html', context)

@csrf_protect
def vet_commentary_request_ack(request, commentary_id):
    if request.method == 'POST':
        form = VetCommentaryForm(request.POST)
        commentary = Commentary.objects.get(pk=commentary_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the commentary as is
                commentary.vetted = True
                commentary.save()
            elif form.cleaned_data['action_option'] == '0':
                # re-edit the form starting from the data provided
                form2 = RequestCommentaryForm(initial={'pub_title': commentary.pub_title, 'arxiv_link': commentary.arxiv_link, 'pub_DOI_link': commentary.pub_DOI_link, 'author_list': commentary.author_list, 'pub_date': commentary.pub_date, 'pub_abstract': commentary.pub_abstract})
                commentary.delete()
                context = {'form': form2 }
                return render(request, 'commentaries/request_commentary.html', context)
            elif form.cleaned_data['action_option'] == '2':
                # the commentary request is simply rejected
                # email Contributor about it...
                commentary.delete()

#    context = {'option': form.cleaned_data['action_option'], 'reason': form.cleaned_data['refusal_reason'] }
    context = { }
    return render(request, 'commentaries/vet_commentary_request_ack.html', context)




@csrf_protect
def commentaries(request):
    if request.method == 'POST':
        form = CommentarySearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            commentary_search_list = Commentary.objects.filter(
                pub_title__contains=form.cleaned_data['pub_title_keyword'],
                author_list__contains=form.cleaned_data['pub_author'],
                pub_abstract__contains=form.cleaned_data['pub_abstract_keyword'],
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

@csrf_protect
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
                comment_text = form.cleaned_data['comment_text'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
#            author.nr_comments += 1
            author.nr_comments = Comment.objects.filter(author=author).count()
            author.save()
            request.session['commentary_id'] = commentary_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    comment_rating_form = CommentRatingForm()
    commentary_rating_form = CommentaryRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(commentary=commentary)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'commentary': commentary, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'author_replies': author_replies, 'form': form, 'commentary_rating_form': commentary_rating_form, 'comment_rating_form': comment_rating_form}
    return render(request, 'commentaries/commentary_detail.html', context)
