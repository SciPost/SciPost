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


###############
# SUBMISSIONS:
###############

def sub_and_ref_procedure(request):
    return render(request, 'submissions/sub_and_ref_procedure.html')

@csrf_protect
def submit_manuscript(request):
    # If POST, process the form data
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submitted_by = Contributor.objects.get(user=request.user)
            submission = Submission (
                submitted_by = submitted_by,
                submitted_to_journal = form.cleaned_data['submitted_to_journal'],
                domain = form.cleaned_data['domain'],
                specialization = form.cleaned_data['specialization'],
                status = '0', 
                title = form.cleaned_data['title'],
                author_list = form.cleaned_data['author_list'],
                abstract = form.cleaned_data['abstract'],
                arxiv_link = form.cleaned_data['arxiv_link'],
                submission_date = timezone.now(),
                )
            submission.save()
            return HttpResponseRedirect(reverse('submissions:submit_manuscript_ack'))
    else:
        form = SubmissionForm()
    return render(request, 'submissions/submit_manuscript.html', {'form': form})

@csrf_protect
def submit_manuscript_ack(request):
    return render(request, 'submissions/submit_manuscript_ack.html')

@csrf_protect
def process_new_submissions(request):
    submissions_to_process = Submission.objects.filter(status='0')
    form = ProcessSubmissionForm()
    context = {'submissions_to_process': submissions_to_process, 'form': form }
    return render(request, 'submissions/process_new_submissions.html', context)

@csrf_protect
def process_new_submission_ack(request, submission_id):
    if request.method == 'POST':
        form = ProcessSubmissionForm(request.POST)
        if form.is_valid():
            submission = Submission.objects.get(pk=submission_id)
            submission.vetted = True
            submission.editor_in_charge = form.cleaned_data['editor_in_charge']
            submission.status = 1
            submission.save()

    context = {}
    return render(request, 'submissions/process_new_submission_ack.html', context)

@csrf_protect
def submissions(request):
    if request.method == 'POST':
        form = SubmissionSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            submission_search_list = Submission.objects.filter(
                title__contains=form.cleaned_data['title_keyword'],
                author_list__contains=form.cleaned_data['author'],
                abstract__contains=form.cleaned_data['abstract_keyword'],
                status__gte=1,
                )
            submission_search_list.order_by('-pub_date')
        else:
            submission_search_list = [] 
           
    else:
        form = SubmissionSearchForm()
        submission_search_list = []

    submission_recent_list = Submission.objects.filter(status__gte=1, latest_activity__gte=timezone.now() + datetime.timedelta(days=-7))
    submission_recent_list = Submission.objects.filter(status__gte=1)
    context = {'form': form, 'submission_search_list': submission_search_list, 'submission_recent_list': submission_recent_list }
    return render(request, 'submissions/submissions.html', context)


@csrf_protect
def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    comments = submission.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newcomment = Comment (
                submission = submission,
                in_reply_to = None,
                author = author,
                comment_text = form.cleaned_data['comment_text'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
            author.nr_comments += 1
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    reports = submission.report_set.all()
    report_rating_form = ReportRatingForm()
    comment_rating_form = CommentRatingForm()
    submission_rating_form = SubmissionRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(submission=submission)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'submission': submission, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'reports': reports.filter(status__gte=1), 'author_replies': author_replies, 'form': form, 'report_rating_form': report_rating_form, 'submission_rating_form': submission_rating_form, 'comment_rating_form': comment_rating_form}
    return render(request, 'submissions/submission_detail.html', context)


