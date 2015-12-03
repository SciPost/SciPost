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




@csrf_protect
def vote_on_commentary(request, commentary_id):
    commentary = get_object_or_404(Commentary, pk=commentary_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = CommentaryRatingForm(request.POST)
        if form.is_valid():
#            if rater.id != report.author.id:
            # Any previous rating from this contributor for this report is deleted:
            CommentaryRating.objects.filter(rater=rater, commentary=commentary).delete()
            newrating = CommentaryRating (
                commentary = commentary,
                rater = Contributor.objects.get(user=request.user),
                clarity = form.cleaned_data['clarity'],
                correctness = form.cleaned_data['correctness'],
                usefulness = form.cleaned_data['usefulness'],
                )
            newrating.save()
            commentary.nr_ratings = CommentaryRating.objects.filter(commentary=commentary).count()
            commentary.save()
            # Recalculate the ratings for this report:
            commentary.clarity_rating = CommentaryRating.objects.filter(commentary=commentary).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            commentary.correctness_rating = CommentaryRating.objects.filter(commentary=commentary).aggregate(avg_correctness=Avg('correctness'))['avg_correctness']
            commentary.usefulness_rating = CommentaryRating.objects.filter(commentary=commentary).aggregate(avg_usefulness=Avg('usefulness'))['avg_usefulness']
            commentary.save()
            return HttpResponseRedirect(reverse('ratings:vote_on_commentary_ack'))

    return render(request, 'ratings/vote_on_commentary_ack.html')
            
def vote_on_commentary_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_commentary_ack.html', context)


@csrf_protect
def vote_on_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = CommentRatingForm(request.POST)
        if form.is_valid():
            if rater.id != comment.author.id:
                # Any previous rating from this contributor for this comment is deleted:
                CommentRating.objects.filter(rater=rater, comment=comment).delete()
                newrating = CommentRating (
                    comment = comment,
                    rater = Contributor.objects.get(user=request.user),
                    clarity = form.cleaned_data['clarity'],
                    correctness = form.cleaned_data['correctness'],
                    usefulness = form.cleaned_data['usefulness'],
                    )
                newrating.save()
#                comment.nr_ratings += 1
                comment.nr_ratings = CommentRating.objects.filter(comment=comment).count()
                comment.save()
                # Recalculate the ratings for this comment:
                comment.clarity_rating = CommentRating.objects.filter(comment=comment).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                comment.correctness_rating = CommentRating.objects.filter(comment=comment).aggregate(avg_correctness=Avg('correctness'))['avg_correctness']
                comment.usefulness_rating = CommentRating.objects.filter(comment=comment).aggregate(avg_usefulness=Avg('usefulness'))['avg_usefulness']
                comment.save()
                # Recalculate the comment_ratings for the comment's author:
                comment.author.comment_clarity_rating = 0
                comment.author.comment_correctness_rating = 0
                comment.author.comment_usefulness_rating = 0
                nr_ratings_author = 0
                clarity_rating_sum_author = 0
                correctness_rating_sum_author = 0
                usefulness_rating_sum_author = 0
                comments_from_author = Comment.objects.filter(author=comment.author)
                for com in comments_from_author:
                    nr_ratings_author += com.nr_ratings
                    clarity_rating_sum_author += com.nr_ratings * com.clarity_rating
                    correctness_rating_sum_author += com.nr_ratings * com.correctness_rating
                    usefulness_rating_sum_author += com.nr_ratings * com.usefulness_rating
                comment.author.comment_clarity_rating = clarity_rating_sum_author/max(1, nr_ratings_author)
                comment.author.comment_correctness_rating = correctness_rating_sum_author/max(1, nr_ratings_author)
                comment.author.comment_usefulness_rating = usefulness_rating_sum_author/max(1, nr_ratings_author)
                comment.author.save()
#            request.session['commentary_id'] = commentary_id
            return HttpResponseRedirect(reverse('ratings:vote_on_comment_ack'))

#    commentary = Commentary(pk=commentary_id)
#    comments = commentary.comment_set.all()
#    form = CommentForm()
#    comment_rating_form = CommentRatingForm()
    
#    context = {'commentary': commentary, 'comments': comments.order_by('date_submitted'), 'form': form, 'comment_rating_form': comment_rating_form}
#    return render(request, 'ratings/commentary_detail.html', context)
    return render(request, 'ratings/vote_on_comment_ack.html')

@csrf_protect            
def vote_on_comment_ack(request):
#    context = {'commentary_id': request.session['commentary_id']}
    context = {}
    return render(request, 'ratings/vote_on_comment_ack.html', context)


@csrf_protect
def vote_on_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = ReportRatingForm(request.POST)
        if form.is_valid():
            if rater.id != report.author.id:
                # Any previous rating from this contributor for this report is deleted:
                ReportRating.objects.filter(rater=rater, report=report).delete()
                newrating = ReportRating (
                    report = report,
                    rater = Contributor.objects.get(user=request.user),
                    clarity = form.cleaned_data['clarity'],
                    correctness = form.cleaned_data['correctness'],
                    usefulness = form.cleaned_data['usefulness'],
                    )
                newrating.save()
#                comment.nr_ratings += 1
                report.nr_ratings = ReportRating.objects.filter(report=report).count()
                report.save()
                # Recalculate the ratings for this report:
                report.clarity_rating = ReportRating.objects.filter(report=report).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                report.correctness_rating = ReportRating.objects.filter(report=report).aggregate(avg_correctness=Avg('correctness'))['avg_correctness']
                report.usefulness_rating = ReportRating.objects.filter(report=report).aggregate(avg_usefulness=Avg('usefulness'))['avg_usefulness']
                report.save()
                # Recalculate the report_ratings for the report's author:
                report.author.report_clarity_rating = 0
                report.author.report_correctness_rating = 0
                report.author.report_usefulness_rating = 0
                nr_ratings_author = 0
                clarity_rating_sum_author = 0
                correctness_rating_sum_author = 0
                usefulness_rating_sum_author = 0
                reports_from_author = Report.objects.filter(author=report.author)
                for rep in reports_from_author:
                    nr_ratings_author += rep.nr_ratings
                    clarity_rating_sum_author += rep.nr_ratings * rep.clarity_rating
                    correctness_rating_sum_author += rep.nr_ratings * rep.correctness_rating
                    usefulness_rating_sum_author += rep.nr_ratings * rep.usefulness_rating
                report.author.report_clarity_rating = clarity_rating_sum_author/max(1, nr_ratings_author)
                report.author.report_correctness_rating = correctness_rating_sum_author/max(1, nr_ratings_author)
                report.author.report_usefulness_rating = usefulness_rating_sum_author/max(1, nr_ratings_author)
                report.author.save()
            return HttpResponseRedirect(reverse('ratings:vote_on_report_ack'))

    return render(request, 'ratings/vote_on_report_ack.html')
            
def vote_on_report_ack(request):
#    context = {'commentary_id': request.session['commentary_id']}
    context = {}
    return render(request, 'ratings/vote_on_report_ack.html', context)



@csrf_protect
def vote_on_submission(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = SubmissionRatingForm(request.POST)
        if form.is_valid():
#            if rater.id != report.author.id:
            # Any previous rating from this contributor for this report is deleted:
            SubmissionRating.objects.filter(rater=rater, submission=submission).delete()
            newrating = SubmissionRating (
                submission = submission,
                rater = Contributor.objects.get(user=request.user),
                clarity = form.cleaned_data['clarity'],
                correctness = form.cleaned_data['correctness'],
                usefulness = form.cleaned_data['usefulness'],
                )
            newrating.save()
            submission.nr_ratings = SubmissionRating.objects.filter(submission=submission).count()
            submission.save()
            # Recalculate the ratings for this report:
            submission.clarity_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            submission.correctness_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_correctness=Avg('correctness'))['avg_correctness']
            submission.usefulness_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_usefulness=Avg('usefulness'))['avg_usefulness']
            submission.save()
            return HttpResponseRedirect(reverse('ratings:vote_on_submission_ack'))

    return render(request, 'ratings/vote_on_submission_ack.html')
            
def vote_on_submission_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_submission_ack.html', context)


