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



def vote_on_commentary(request, commentary_id):
    commentary = get_object_or_404(Commentary, pk=commentary_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = CommentaryRatingForm(request.POST)
        if form.is_valid():
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
            # Recalculate the ratings for this commentary:
            commentary.clarity_rating = CommentaryRating.objects.filter(commentary=commentary, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            commentary.validity_rating = CommentaryRating.objects.filter(commentary=commentary, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
            commentary.rigour_rating = CommentaryRating.objects.filter(commentary=commentary, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
            commentary.originality_rating = CommentaryRating.objects.filter(commentary=commentary, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
            commentary.significance_rating = CommentaryRating.objects.filter(commentary=commentary, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
            commentary.save()
            context = {'commentary_id': commentary_id}
            return render(request, 'ratings/vote_on_commentary_ack.html', context)

    context = {'commentary_id': commentary_id}
    return render(request, 'ratings/vote_on_commentary_ack.html', context)
            
def vote_on_commentary_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_commentary_ack.html', context)



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
                    relevance = form.cleaned_data['relevance'],
                    importance = form.cleaned_data['importance'],
                    clarity = form.cleaned_data['clarity'],
                    validity = form.cleaned_data['validity'],
                    rigour = form.cleaned_data['rigour'],
                )
                newrating.save()

                comment.nr_relevance_ratings = CommentRating.objects.filter(comment=comment, relevance__lte=100).count()
                comment.nr_importance_ratings = CommentRating.objects.filter(comment=comment, importance__lte=100).count()
                comment.nr_clarity_ratings = CommentRating.objects.filter(comment=comment, clarity__lte=100).count()
                comment.nr_validity_ratings = CommentRating.objects.filter(comment=comment, validity__lte=100).count()
                comment.nr_rigour_ratings = CommentRating.objects.filter(comment=comment, rigour__lte=100).count()
                comment.save()

                # Recalculate the ratings for this comment:
                comment.relevance_rating = CommentRating.objects.filter(comment=comment, relevance__lte=100).aggregate(avg_relevance=Avg('relevance'))['avg_relevance']
                comment.importance_rating = CommentRating.objects.filter(comment=comment, importance__lte=100).aggregate(avg_importance=Avg('importance'))['avg_importance']
                comment.clarity_rating = CommentRating.objects.filter(comment=comment, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                comment.validity_rating = CommentRating.objects.filter(comment=comment, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
                comment.rigour_rating = CommentRating.objects.filter(comment=comment, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
                comment.save()

                # Recalculate the comment_ratings for the comment's author:
                comment.author.comment_relevance_rating = 0
                comment.author.comment_importance_rating = 0 
                comment.author.comment_clarity_rating = 0
                comment.author.comment_validity_rating = 0
                comment.author.comment_rigour_rating = 0

                nr_relevance_ratings_author = 0
                nr_importance_ratings_author = 0
                nr_clarity_ratings_author = 0
                nr_validity_ratings_author = 0
                nr_rigour_ratings_author = 0
                relevance_rating_sum_author = 0
                importance_rating_sum_author = 0
                clarity_rating_sum_author = 0
                validity_rating_sum_author = 0
                rigour_rating_sum_author = 0

                comments_from_author = Comment.objects.filter(author=comment.author)
                for com in comments_from_author:
                    nr_relevance_ratings_author += com.nr_relevance_ratings
                    if com.nr_relevance_ratings > 0:
                        relevance_rating_sum_author += com.nr_relevance_ratings * com.relevance_rating
                    nr_importance_ratings_author += com.nr_importance_ratings
                    if com.nr_importance_ratings > 0:
                        importance_rating_sum_author += com.nr_importance_ratings * com.importance_rating
                    nr_clarity_ratings_author += com.nr_clarity_ratings
                    if com.nr_clarity_ratings > 0:
                        clarity_rating_sum_author += com.nr_clarity_ratings * com.clarity_rating
                    nr_validity_ratings_author += com.nr_validity_ratings
                    if com.nr_validity_ratings > 0:
                        validity_rating_sum_author += com.nr_validity_ratings * com.validity_rating
                    nr_rigour_ratings_author += com.nr_rigour_ratings
                    if com.nr_rigour_ratings > 0:
                        rigour_rating_sum_author += com.nr_rigour_ratings * com.rigour_rating

                comment.author.nr_comment_relevance_ratings = nr_relevance_ratings_author
                comment.author.comment_relevance_rating = relevance_rating_sum_author/max(1, nr_relevance_ratings_author)
                comment.author.nr_comment_importance_ratings = nr_importance_ratings_author
                comment.author.comment_importance_rating = importance_rating_sum_author/max(1, nr_importance_ratings_author)
                comment.author.nr_comment_clarity_ratings = nr_clarity_ratings_author
                comment.author.comment_clarity_rating = clarity_rating_sum_author/max(1, nr_clarity_ratings_author)
                comment.author.nr_comment_validity_ratings = nr_validity_ratings_author
                comment.author.comment_validity_rating = validity_rating_sum_author/max(1, nr_validity_ratings_author)
                comment.author.nr_comment_rigour_ratings = nr_rigour_ratings_author
                comment.author.comment_rigour_rating = rigour_rating_sum_author/max(1, nr_rigour_ratings_author)

                comment.author.save()

            return HttpResponseRedirect(reverse('ratings:vote_on_comment_ack'))

    return render(request, 'ratings/vote_on_comment_ack.html')


def vote_on_comment_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_comment_ack.html', context)


def vote_on_authorreply(request, authorreply_id):
    authorreply = get_object_or_404(AuthorReply, pk=authorreply_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = AuthorReplyRatingForm(request.POST)
        if form.is_valid():
            if rater.id != authorreply.author.id:
                # Any previous rating from this contributor for this authorreply is deleted:
                AuthorReplyRating.objects.filter(rater=rater, authorreply=authorreply).delete()
                newrating = AuthorReplyRating (
                    authorreply = authorreply,
                    rater = Contributor.objects.get(user=request.user),
                    relevance = form.cleaned_data['relevance'],
                    importance = form.cleaned_data['importance'],
                    clarity = form.cleaned_data['clarity'],
                    validity = form.cleaned_data['validity'],
                    rigour = form.cleaned_data['rigour'],
                )
                newrating.save()

                authorreply.nr_relevance_ratings = AuthorReplyRating.objects.filter(authorreply=authorreply, relevance__lte=100).count()
                authorreply.nr_importance_ratings = AuthorReplyRating.objects.filter(authorreply=authorreply, importance__lte=100).count()
                authorreply.nr_clarity_ratings = AuthorReplyRating.objects.filter(authorreply=authorreply, clarity__lte=100).count()
                authorreply.nr_validity_ratings = AuthorReplyRating.objects.filter(authorreply=authorreply, validity__lte=100).count()
                authorreply.nr_rigour_ratings = AuthorReplyRating.objects.filter(authorreply=authorreply, rigour__lte=100).count()
                authorreply.save()

                # Recalculate the ratings for this authorreply:
                authorreply.relevance_rating = AuthorReplyRating.objects.filter(authorreply=authorreply, relevance__lte=100).aggregate(avg_relevance=Avg('relevance'))['avg_relevance']
                authorreply.importance_rating = AuthorReplyRating.objects.filter(authorreply=authorreply, importance__lte=100).aggregate(avg_importance=Avg('importance'))['avg_importance']
                authorreply.clarity_rating = AuthorReplyRating.objects.filter(authorreply=authorreply, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                authorreply.validity_rating = AuthorReplyRating.objects.filter(authorreply=authorreply, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
                authorreply.rigour_rating = AuthorReplyRating.objects.filter(authorreply=authorreply, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
                authorreply.save()

                # Recalculate the authorreply_ratings for the authorreply's author:
                authorreply.author.authorreply_relevance_rating = 0
                authorreply.author.authorreply_importance_rating = 0 
                authorreply.author.authorreply_clarity_rating = 0
                authorreply.author.authorreply_validity_rating = 0
                authorreply.author.authorreply_rigour_rating = 0

                nr_relevance_ratings_author = 0
                nr_importance_ratings_author = 0
                nr_clarity_ratings_author = 0
                nr_validity_ratings_author = 0
                nr_rigour_ratings_author = 0
                relevance_rating_sum_author = 0
                importance_rating_sum_author = 0
                clarity_rating_sum_author = 0
                validity_rating_sum_author = 0
                rigour_rating_sum_author = 0

                authorreplys_from_author = AuthorReply.objects.filter(author=authorreply.author)
                for com in authorreplys_from_author:
                    nr_relevance_ratings_author += com.nr_relevance_ratings
                    if com.nr_relevance_ratings > 0:
                        relevance_rating_sum_author += com.nr_relevance_ratings * com.relevance_rating
                    nr_importance_ratings_author += com.nr_importance_ratings
                    if com.nr_importance_ratings > 0:
                        importance_rating_sum_author += com.nr_importance_ratings * com.importance_rating
                    nr_clarity_ratings_author += com.nr_clarity_ratings
                    if com.nr_clarity_ratings > 0:
                        clarity_rating_sum_author += com.nr_clarity_ratings * com.clarity_rating
                    nr_validity_ratings_author += com.nr_validity_ratings
                    if com.nr_validity_ratings > 0:
                        validity_rating_sum_author += com.nr_validity_ratings * com.validity_rating
                    nr_rigour_ratings_author += com.nr_rigour_ratings
                    if com.nr_rigour_ratings > 0:
                        rigour_rating_sum_author += com.nr_rigour_ratings * com.rigour_rating

                authorreply.author.nr_authorreply_relevance_ratings = nr_relevance_ratings_author
                authorreply.author.authorreply_relevance_rating = relevance_rating_sum_author/max(1, nr_relevance_ratings_author)
                authorreply.author.nr_authorreply_importance_ratings = nr_importance_ratings_author
                authorreply.author.authorreply_importance_rating = importance_rating_sum_author/max(1, nr_importance_ratings_author)
                authorreply.author.nr_authorreply_clarity_ratings = nr_clarity_ratings_author
                authorreply.author.authorreply_clarity_rating = clarity_rating_sum_author/max(1, nr_clarity_ratings_author)
                authorreply.author.nr_authorreply_validity_ratings = nr_validity_ratings_author
                authorreply.author.authorreply_validity_rating = validity_rating_sum_author/max(1, nr_validity_ratings_author)
                authorreply.author.nr_authorreply_rigour_ratings = nr_rigour_ratings_author
                authorreply.author.authorreply_rigour_rating = rigour_rating_sum_author/max(1, nr_rigour_ratings_author)

                authorreply.author.save()

            return HttpResponseRedirect(reverse('ratings:vote_on_authorreply_ack'))

    return render(request, 'ratings/vote_on_authorreply_ack.html')


def vote_on_authorreply_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_authorreply_ack.html', context)



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
                    relevance = form.cleaned_data['relevance'],
                    importance = form.cleaned_data['importance'],
                    clarity = form.cleaned_data['clarity'],
                    validity = form.cleaned_data['validity'],
                    rigour = form.cleaned_data['rigour'],
                    )
                newrating.save()

                report.nr_relevance_ratings = ReportRating.objects.filter(report=report, relevance__lte=100).count()
                report.nr_importance_ratings = ReportRating.objects.filter(report=report, importance__lte=100).count()
                report.nr_clarity_ratings = ReportRating.objects.filter(report=report, clarity__lte=100).count()
                report.nr_validity_ratings = ReportRating.objects.filter(report=report, validity__lte=100).count()
                report.nr_rigour_ratings = ReportRating.objects.filter(report=report, rigour__lte=100).count()
                report.save()
                # Recalculate the ratings for this report:
                report.relevance_rating = ReportRating.objects.filter(report=report, relevance__lte=100).aggregate(avg_relevance=Avg('relevance'))['avg_relevance']
                report.importance_rating = ReportRating.objects.filter(report=report, importance__lte=100).aggregate(avg_importance=Avg('importance'))['avg_importance']
                report.clarity_rating = ReportRating.objects.filter(report=report, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
                report.validity_rating = ReportRating.objects.filter(report=report, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
                report.rigour_rating = ReportRating.objects.filter(report=report, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
                report.save()

                # Recalculate the report_ratings for the report's author:
                report.author.report_relevance_rating = 0
                report.author.report_importance_rating = 0
                report.author.report_clarity_rating = 0
                report.author.report_validity_rating = 0
                report.author.report_rigour_rating = 0

                nr_relevance_ratings_author = 0
                nr_importance_ratings_author = 0
                nr_clarity_ratings_author = 0
                nr_validity_ratings_author = 0
                nr_rigour_ratings_author = 0
                relevance_rating_sum_author = 0
                importance_rating_sum_author = 0
                clarity_rating_sum_author = 0
                validity_rating_sum_author = 0
                rigour_rating_sum_author = 0

                reports_from_author = Report.objects.filter(author=report.author)
                for rep in reports_from_author:
                    nr_relevance_ratings_author += rep.nr_relevance_ratings
                    if rep.nr_relevance_ratings > 0:
                        relevance_rating_sum_author += rep.nr_relevance_ratings * rep.relevance_rating
                    nr_importance_ratings_author += rep.nr_importance_ratings
                    if rep.nr_importance_ratings > 0:
                        importance_rating_sum_author += rep.nr_importance_ratings * rep.importance_rating
                    nr_clarity_ratings_author += rep.nr_clarity_ratings
                    if rep.nr_clarity_ratings > 0:
                        clarity_rating_sum_author += rep.nr_clarity_ratings * rep.clarity_rating
                    nr_validity_ratings_author += rep.nr_validity_ratings
                    if rep.nr_validity_ratings > 0:
                        clarity_rating_sum_author += rep.nr_validity_ratings * rep.validity_rating
                    nr_rigour_ratings_author += rep.nr_rigour_ratings
                    if rep.nr_rigour_ratings > 0:
                        rigour_rating_sum_author += rep.nr_rigour_ratings * rep.rigour_rating

                report.author.nr_report_relevance_ratings = nr_relevance_ratings_author
                report.author.report_relevance_rating = relevance_rating_sum_author/max(1, nr_relevance_ratings_author)
                report.author.nr_report_importance_ratings = nr_importance_ratings_author
                report.author.report_importance_rating = importance_rating_sum_author/max(1, nr_importance_ratings_author)
                report.author.nr_report_clarity_ratings = nr_clarity_ratings_author
                report.author.report_clarity_rating = clarity_rating_sum_author/max(1, nr_clarity_ratings_author)
                report.author.nr_report_validity_ratings = nr_validity_ratings_author
                report.author.report_validity_rating = validity_rating_sum_author/max(1, nr_validity_ratings_author)
                report.author.nr_report_rigour_ratings = nr_rigour_ratings_author
                report.author.report_rigour_rating = rigour_rating_sum_author/max(1, nr_rigour_ratings_author)

                report.author.save()
            return HttpResponseRedirect(reverse('ratings:vote_on_report_ack'))

    return render(request, 'ratings/vote_on_report_ack.html')
            
def vote_on_report_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_report_ack.html', context)




def vote_on_submission(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = SubmissionRatingForm(request.POST)
        if form.is_valid():
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

            submission.nr_clarity_ratings = SubmissionRating.objects.filter(submission=submission, clarity__lte=100).count()
            submission.nr_validity_ratings = SubmissionRating.objects.filter(submission=submission, validity__lte=100).count()
            submission.nr_rigour_ratings = SubmissionRating.objects.filter(submission=submission, rigour__lte=100).count()
            submission.nr_originality_ratings = SubmissionRating.objects.filter(submission=submission, originality__lte=100).count()
            submission.nr_significance_ratings = SubmissionRating.objects.filter(submission=submission, significance__lte=100).count()
            submission.save()

            # Recalculate the ratings for this report:
            submission.clarity_rating = SubmissionRating.objects.filter(submission=submission, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            submission.validity_rating = SubmissionRating.objects.filter(submission=submission, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
            submission.rigour_rating = SubmissionRating.objects.filter(submission=submission, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
            submission.originality_rating = SubmissionRating.objects.filter(submission=submission, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
            submission.significance_rating = SubmissionRating.objects.filter(submission=submission, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
            submission.save()
            context = {'submission_id': submission_id}
            return render(request, 'ratings/vote_on_submission_ack.html', context)

    context = {'submission_id': submission_id}
    return render(request, 'ratings/vote_on_submission_ack.html', context)
            
def vote_on_submission_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_submission_ack.html', context)


def vote_on_thesis(request, thesislink_id):
    thesislink = get_object_or_404(ThesisLink, pk=thesislink_id)
    rater = Contributor.objects.get(user=request.user)
    if request.method == 'POST':
        form = ThesisLinkRatingForm(request.POST)
        if form.is_valid():
            # Any previous rating from this contributor for this report is deleted:
            ThesisLinkRating.objects.filter(rater=rater, thesislink=thesislink).delete()
            newrating = ThesisLinkRating (
                thesislink = thesislink,
                rater = Contributor.objects.get(user=request.user),
                clarity = form.cleaned_data['clarity'],
                validity = form.cleaned_data['validity'],
                rigour = form.cleaned_data['rigour'],
                originality = form.cleaned_data['originality'],
                significance = form.cleaned_data['significance'],
                )
            newrating.save()
            thesislink.nr_clarity_ratings = ThesisLinkRating.objects.filter(thesislink=thesislink, clarity__lte=100).count()
            thesislink.nr_validity_ratings = ThesisLinkRating.objects.filter(thesislink=thesislink, validity__lte=100).count()
            thesislink.nr_rigour_ratings = ThesisLinkRating.objects.filter(thesislink=thesislink, rigour__lte=100).count()
            thesislink.nr_originality_ratings = ThesisLinkRating.objects.filter(thesislink=thesislink, originality__lte=100).count()
            thesislink.nr_significance_ratings = ThesisLinkRating.objects.filter(thesislink=thesislink, significance__lte=100).count()
            thesislink.save()
            # Recalculate the ratings for this thesislink:
            thesislink.clarity_rating = ThesisLinkRating.objects.filter(thesislink=thesislink, clarity__lte=100).aggregate(avg_clarity=Avg('clarity'))['avg_clarity']
            thesislink.validity_rating = ThesisLinkRating.objects.filter(thesislink=thesislink, validity__lte=100).aggregate(avg_validity=Avg('validity'))['avg_validity']
            thesislink.rigour_rating = ThesisLinkRating.objects.filter(thesislink=thesislink, rigour__lte=100).aggregate(avg_rigour=Avg('rigour'))['avg_rigour']
            thesislink.originality_rating = ThesisLinkRating.objects.filter(thesislink=thesislink, originality__lte=100).aggregate(avg_originality=Avg('originality'))['avg_originality']
            thesislink.significance_rating = ThesisLinkRating.objects.filter(thesislink=thesislink, significance__lte=100).aggregate(avg_significance=Avg('significance'))['avg_significance']
            thesislink.save()
            context = {'thesislink_id': thesislink_id}
            return render(request, 'ratings/vote_on_thesis_ack.html', context)

    context = {'thesislink_id': thesislink_id}
    return render(request, 'ratings/vote_on_thesis_ack.html', context)
            
def vote_on_thesis_ack(request):
    context = {}
    return render(request, 'ratings/vote_on_thesis_ack.html', context)

