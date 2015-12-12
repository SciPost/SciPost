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
                validity = form.cleaned_data['validity'],
                rigour = form.cleaned_data['rigour'],
                originality = form.cleaned_data['originality'],
                significance = form.cleaned_data['significance'],
                )
            newrating.save()
            commentary.nr_clarity_ratings = CommentaryRating.objects.filter(commentary=commentary, clarity__lte=100).count()
            commentary.nr_validity_ratings = CommentaryRating.objects.filter(commentary=commentary, validity__lte=100).count()
            commentary.nr_rigour_ratings = CommentaryRating.objects.filter(commentary=commentary, rigour__lte=100).count()
            commentary.nr_originality_ratings = CommentaryRating.objects.filter(commentary=commentary, originality__lte=100).count()
            commentary.nr_significance_ratings = CommentaryRating.objects.filter(commentary=commentary, significance__lte=100).count()
            commentary.save()
            # Recalculate the ratings for this report:
            commentary.clarity_rating = CommentaryRating.objects.filter(commentary=commentary, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            commentary.validity_rating = CommentaryRating.objects.filter(commentary=commentary, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
            commentary.rigour_rating = CommentaryRating.objects.filter(commentary=commentary, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
            commentary.originality_rating = CommentaryRating.objects.filter(commentary=commentary, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
            commentary.significance_rating = CommentaryRating.objects.filter(commentary=commentary, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
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
                    validity = form.cleaned_data['validity'],
                    rigour = form.cleaned_data['rigour'],
                    originality = form.cleaned_data['originality'],
                    significance = form.cleaned_data['significance'],
                )
                newrating.save()

                comment.nr_clarity_ratings = CommentRating.objects.filter(comment=comment, clarity__lte=100).count()
                comment.nr_validity_ratings = CommentRating.objects.filter(comment=comment, validity__lte=100).count()
                comment.nr_rigour_ratings = CommentRating.objects.filter(comment=comment, rigour__lte=100).count()
                comment.nr_originality_ratings = CommentRating.objects.filter(comment=comment, originality__lte=100).count()
                comment.nr_significance_ratings = CommentRating.objects.filter(comment=comment, significance__lte=100).count()
                comment.save()
                # Recalculate the ratings for this comment:
                comment.clarity_rating = CommentRating.objects.filter(comment=comment, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                comment.validity_rating = CommentRating.objects.filter(comment=comment, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
                comment.rigour_rating = CommentRating.objects.filter(comment=comment, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
                comment.originality_rating = CommentRating.objects.filter(comment=comment, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
                comment.significance_rating = CommentRating.objects.filter(comment=comment, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
                comment.save()
                # Recalculate the comment_ratings for the comment's author:
                comment.author.comment_clarity_rating = 0
                comment.author.comment_validity_rating = 0
                comment.author.comment_rigour_rating = 0
                comment.author.comment_originality_rating = 0
                comment.author.comment_significance_rating = 0

                nr_clarity_ratings_author = 0
                nr_validity_ratings_author = 0
                nr_rigour_ratings_author = 0
                nr_originality_ratings_author = 0
                nr_significance_ratings_author = 0
                clarity_rating_sum_author = 0
                validity_rating_sum_author = 0
                rigour_rating_sum_author = 0
                originality_rating_sum_author = 0
                significance_rating_sum_author = 0

                comments_from_author = Comment.objects.filter(author=comment.author)
                for com in comments_from_author:
                    nr_clarity_ratings_author += com.nr_clarity_ratings
                    if com.nr_clarity_ratings > 0:
                        clarity_rating_sum_author += com.nr_clarity_ratings * com.clarity_rating
                    nr_validity_ratings_author += com.nr_validity_ratings
                    if com.nr_validity_ratings > 0:
                        clarity_rating_sum_author += com.nr_validity_ratings * com.validity_rating
                    nr_rigour_ratings_author += com.nr_rigour_ratings
                    if com.nr_rigour_ratings > 0:
                        rigour_rating_sum_author += com.nr_rigour_ratings * com.rigour_rating
                    nr_originality_ratings_author += com.nr_originality_ratings
                    if com.nr_originality_ratings > 0:
                        originality_rating_sum_author += com.nr_originality_ratings * com.originality_rating
                    nr_significance_ratings_author += com.nr_significance_ratings
                    if com.nr_significance_ratings > 0:
                        significance_rating_sum_author += com.nr_significance_ratings * com.significance_rating

                comment.author.comment_clarity_rating = clarity_rating_sum_author/max(1, nr_clarity_ratings_author)
                comment.author.comment_validity_rating = validity_rating_sum_author/max(1, nr_validity_ratings_author)
                comment.author.comment_rigour_rating = rigour_rating_sum_author/max(1, nr_rigour_ratings_author)
                comment.author.comment_originality_rating = originality_rating_sum_author/max(1, nr_originality_ratings_author)
                comment.author.comment_significance_rating = significance_rating_sum_author/max(1, nr_significance_ratings_author)

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
                    validity = form.cleaned_data['validity'],
                    rigour = form.cleaned_data['rigour'],
                    originality = form.cleaned_data['originality'],
                    significance = form.cleaned_data['significance'],
                    )
                newrating.save()

                report.nr_clarity_ratings = ReportRating.objects.filter(report=report, clarity__lte=100).count()
                report.nr_validity_ratings = ReportRating.objects.filter(report=report, validity__lte=100).count()
                report.nr_rigour_ratings = ReportRating.objects.filter(report=report, rigour__lte=100).count()
                report.nr_originality_ratings = ReportRating.objects.filter(report=report, originality__lte=100).count()
                report.nr_significance_ratings = ReportRating.objects.filter(report=report, significance__lte=100).count()
                report.save()
                # Recalculate the ratings for this report:
                report.clarity_rating = ReportRating.objects.filter(report=report, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                report.validity_rating = ReportRating.objects.filter(report=report, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
                report.rigour_rating = ReportRating.objects.filter(report=report, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
                report.originality_rating = ReportRating.objects.filter(report=report, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
                report.significance_rating = ReportRating.objects.filter(report=report, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
                report.save()
                # Recalculate the report_ratings for the report's author:
                report.author.report_clarity_rating = 0
                report.author.report_validity_rating = 0
                report.author.report_rigour_rating = 0
                report.author.report_originality_rating = 0
                report.author.report_significance_rating = 0

                nr_clarity_ratings_author = 0
                nr_validity_ratings_author = 0
                nr_rigour_ratings_author = 0
                nr_originality_ratings_author = 0
                nr_significance_ratings_author = 0
                clarity_rating_sum_author = 0
                validity_rating_sum_author = 0
                rigour_rating_sum_author = 0
                originality_rating_sum_author = 0
                significance_rating_sum_author = 0

                reports_from_author = Report.objects.filter(author=report.author)
                for rep in reports_from_author:
                    nr_clarity_ratings_author += rep.nr_clarity_ratings
                    if rep.nr_clarity_ratings > 0:
                        clarity_rating_sum_author += rep.nr_clarity_ratings * rep.clarity_rating
                    nr_validity_ratings_author += rep.nr_validity_ratings
                    if rep.nr_validity_ratings > 0:
                        clarity_rating_sum_author += rep.nr_validity_ratings * rep.validity_rating
                    nr_rigour_ratings_author += rep.nr_rigour_ratings
                    if rep.nr_rigour_ratings > 0:
                        rigour_rating_sum_author += rep.nr_rigour_ratings * rep.rigour_rating
                    nr_originality_ratings_author += rep.nr_originality_ratings
                    if rep.nr_originality_ratings > 0:
                        originality_rating_sum_author += rep.nr_originality_ratings * rep.originality_rating
                    nr_significance_ratings_author += rep.nr_significance_ratings
                    if rep.nr_significance_ratings > 0:
                        significance_rating_sum_author += rep.nr_significance_ratings * rep.significance_rating

                report.author.report_clarity_rating = clarity_rating_sum_author/max(1, nr_clarity_ratings_author)
                report.author.report_validity_rating = validity_rating_sum_author/max(1, nr_validity_ratings_author)
                report.author.report_rigour_rating = rigour_rating_sum_author/max(1, nr_rigour_ratings_author)
                report.author.report_originality_rating = originality_rating_sum_author/max(1, nr_originality_ratings_author)
                report.author.report_significance_rating = significance_rating_sum_author/max(1, nr_significance_ratings_author)

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
                validity = form.cleaned_data['validity'],
                rigour = form.cleaned_data['rigour'],
                originality = form.cleaned_data['originality'],
                significance = form.cleaned_data['significance'],
                )
            newrating.save()
            #submission.nr_ratings = SubmissionRating.objects.filter(submission=submission).count()
            submission.nr_clarity_ratings = SubmissionRating.objects.filter(submission=submission, clarity__lte=100).count()
            submission.nr_validity_ratings = SubmissionRating.objects.filter(submission=submission, validity__lte=100).count()
            submission.nr_rigour_ratings = SubmissionRating.objects.filter(submission=submission, rigour__lte=100).count()
            submission.nr_originality_ratings = SubmissionRating.objects.filter(submission=submission, originality__lte=100).count()
            submission.nr_significance_ratings = SubmissionRating.objects.filter(submission=submission, significance__lte=100).count()
            submission.save()
            # Recalculate the ratings for this report:
#            submission.clarity_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
#            submission.correctness_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_correctness=Avg('correctness'))['avg_correctness']
#            submission.usefulness_rating = SubmissionRating.objects.filter(submission=submission).aggregate(avg_usefulness=Avg('usefulness'))['avg_usefulness']
            submission.clarity_rating = SubmissionRating.objects.filter(submission=submission, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            submission.validity_rating = SubmissionRating.objects.filter(submission=submission, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
            submission.rigour_rating = SubmissionRating.objects.filter(submission=submission, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
            submission.originality_rating = SubmissionRating.objects.filter(submission=submission, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
            submission.significance_rating = SubmissionRating.objects.filter(submission=submission, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
            submission.save()
            return HttpResponseRedirect(reverse('ratings:vote_on_submission_ack'))

    return render(request, 'ratings/vote_on_submission_ack.html')
            
def vote_on_submission_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_submission_ack.html', context)


