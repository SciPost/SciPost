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
from scipost.models import Contributor, title_dict
from submissions.models import Submission

from comments.forms import CommentForm
from ratings.forms import CommentRatingForm, AuthorReplyRatingForm, ReportRatingForm, SubmissionRatingForm



###############
# SUBMISSIONS:
###############

def sub_and_ref_procedure(request):
    return render(request, 'submissions/sub_and_ref_procedure.html')


def submit_manuscript(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submitted_by = Contributor.objects.get(user=request.user)
            submission = Submission (
                submitted_by = submitted_by,
                submitted_to_journal = form.cleaned_data['submitted_to_journal'],
                discipline = form.cleaned_data['discipline'],
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


def submit_manuscript_ack(request):
    return render(request, 'submissions/submit_manuscript_ack.html')


def process_new_submissions(request):
    submission_to_process = Submission.objects.filter(status='0').first() # only handle one at at time
    form = ProcessSubmissionForm()
    context = {'submission_to_process': submission_to_process, 'form': form }
    return render(request, 'submissions/process_new_submissions.html', context)


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


def submissions(request):
    if request.method == 'POST':
        form = SubmissionSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            submission_search_list = Submission.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author_list__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
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


def browse(request, discipline, nrweeksback):
    if request.method == 'POST':
        form = SubmissionSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            submission_search_list = Submission.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author_list__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                vetted=True,
                )
            submission_search_list.order_by('-submission_date')
        else:
            submission_search_list = []
        context = {'form': form, 'submission_search_list': submission_search_list }
        return HttpResponseRedirect(request, 'submissions/submissions.html', context)
    else:
        form = SubmissionSearchForm()
    submission_list = Submission.objects.filter(vetted=True, discipline=discipline, latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback)))
    context = {'form': form, 'discipline': discipline, 'nrweeksback': nrweeksback, 'submission_list': submission_list }
    return render(request, 'submissions/browse.html', context)


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
            author.nr_comments += 1
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    reports = submission.report_set.all()
    report_rating_form = ReportRatingForm()
    comment_rating_form = CommentRatingForm()
    authorreply_rating_form = AuthorReplyRatingForm()
    submission_rating_form = SubmissionRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(submission=submission)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'submission': submission, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'reports': reports.filter(status__gte=1), 'author_replies': author_replies, 'form': form, 'report_rating_form': report_rating_form, 'submission_rating_form': submission_rating_form, 'comment_rating_form': comment_rating_form, 'authorreply_rating_form': authorreply_rating_form}
    return render(request, 'submissions/submission_detail.html', context)



###########
# Reports
###########

def submit_report(request, submission_id):
    submission = get_object_or_404 (Submission, pk=submission_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newreport = Report (
                submission = submission,
                author = author,
                qualification = form.cleaned_data['qualification'],
                strengths = form.cleaned_data['strengths'],
                weaknesses = form.cleaned_data['weaknesses'],
                report = form.cleaned_data['report'],
                requested_changes = form.cleaned_data['requested_changes'],
                formatting = form.cleaned_data['formatting'],
                grammar = form.cleaned_data['grammar'],
                recommendation = form.cleaned_data['recommendation'],
                date_submitted = timezone.now(),
                )
            newreport.save()
            author.nr_reports = Report.objects.filter(author=author).count()
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('reports:submit_report_ack'))

    else:
        form = ReportForm()
    context = {'submission': submission, 'form': form }
    return render(request, 'submissions/submit_report.html', context)


def submit_report_ack(request):
    context = {}
    return render(request, 'submissions/submit_report_ack.html', context)


def vet_submitted_reports(request):
    contributor = Contributor.objects.get(user=request.user)
    report_to_vet = Report.objects.filter(status=0).first() # only handle one at a time
    form = VetReportForm()
    context = {'contributor': contributor, 'report_to_vet': report_to_vet, 'form': form }
    return(render(request, 'submissions/vet_submitted_reports.html', context))


def vet_submitted_report_ack(request, report_id):
    if request.method == 'POST':
        form = VetReportForm(request.POST)
        report = Report.objects.get(pk=report_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the report as is
                report.status = 1
                report.save()
            elif form.cleaned_data['action_option'] == '2':
                # the report is simply rejected
                report.status = form.cleaned_data['refusal_reason']
                report.save()
                # email report author

    context = {}
    return render(request, 'submissions/vet_submitted_report_ack.html', context)

