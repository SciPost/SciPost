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

def index(request):
    return render(request, 'scipost/index.html')

###############
# Information
###############

def about(request):
    return render(request, 'scipost/about.html')

def description(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="SciPost_Description.pdf"'
    return response
#    return HttpResponse("scipost/SciPost_Description.pdf", content_type="application/pdf")

def peer_witnessed_refereeing(request):
    return render(request, 'scipost/peer_witnessed_refereeing.html')

################
# Registration
################

def register(request):
    # If POST, process the form data
    if request.method == 'POST':
        # create a form instance and populate it with the form data
        form = RegistrationForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            # create the user
            user = User.objects.create_user (
                first_name = form.cleaned_data['first_name'],
                last_name = form.cleaned_data['last_name'],
                email = form.cleaned_data['email'],
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password']
                )
            contributor = Contributor (
                user=user, 
                title = form.cleaned_data['title'],
                address = form.cleaned_data['address'],
                affiliation = form.cleaned_data['affiliation'],
                personalwebpage = form.cleaned_data['personalwebpage'],
                )
            contributor.save()
            return HttpResponseRedirect('thanks_for_registering')
    # if GET or other method, create a blank form
    else:
        form = RegistrationForm()

    return render(request, 'scipost/register.html', {'form': form})


def thanks_for_registering(request):
    return render(request, 'scipost/thanks_for_registering.html')

@csrf_protect
def vet_registration_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    registration_requests_to_vet = Contributor.objects.filter(rank=0)
    form = VetRegistrationForm()
    context = {'contributor': contributor, 'registration_requests_to_vet': registration_requests_to_vet, 'form': form }
    return render(request, 'scipost/vet_registration_requests.html', context)

@csrf_protect
def vet_registration_request_ack(request, contributor_id):
    # process the form
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        contributor = Contributor.objects.get(pk=contributor_id)
        if form.is_valid():
            if form.cleaned_data['promote_to_rank_1']:
#            if request.POST['promote_to_rank_1']:
#            if form['promote_to_rank_1']:
                contributor.rank = 1
                contributor.save()
            else:
                #            email_text = 'Dear ' . contributor.title . ' ' . contributor.user.last_name . ', \n Your registration to the SciPost publication portal has been turned down (you can still view all the content, just not submit papers, comments or votes). We nonetheless thank you for your interest. \n\n The SciPost team.' # Syntax error here, don't see it.
                email_text = 'Dear'
            #            send_mail('SciPost registration: unauthorized', email_text, 'admin@scipost.org', [contributor.user.email, 'admin@scipost.org'], fail_silently=False) # Activate later, when scipost email is running
                contributor.rank = form.cleaned_data['refusal_reason']
                contributor.save()

    context = {}
    return render(request, 'scipost/vet_registration_request_ack.html', context)

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                contributor = Contributor.objects.get(user=request.user)
                context = {'contributor': contributor }
                return render(request, 'scipost/personal_page.html', context)
            else:
                return render(request, 'scipost/disabled_account.html')
        else:
            return render(request, 'scipost/login_error.html')
    else:
        form = AuthenticationForm()
        return render(request, 'scipost/login.html', {'form': form})

@csrf_protect
def logout_view(request):
    logout(request)
    return render(request, 'scipost/logout.html')

@csrf_protect
def personal_page(request):
    if request.user.is_authenticated():
        contributor = Contributor.objects.get(user=request.user)
        # if an editor, count the number of actions required:
        nr_reg_to_vet = 0
        nr_submissions_to_process = 0
        if contributor.rank >= 4:
            # count the number of pending registration request
            nr_reg_to_vet = Contributor.objects.filter(rank=0).count()
            nr_submissions_to_process = Submission.objects.filter(vetted=False).count()
        nr_commentary_page_requests_to_vet = 0
        nr_comments_to_vet = 0
        nr_author_replies_to_vet = 0
        nr_reports_to_vet = 0
        if contributor.rank >= 2:
            nr_commentary_page_requests_to_vet = Commentary.objects.filter(vetted=False).count()
            nr_comments_to_vet = Comment.objects.filter(status=0).count()
            nr_author_replies_to_vet = AuthorReply.objects.filter(status=0).count()
            nr_reports_to_vet = Report.objects.filter(status=0).count()
        context = {'contributor': contributor, 'nr_reg_to_vet': nr_reg_to_vet, 'nr_commentary_page_requests_to_vet': nr_commentary_page_requests_to_vet, 'nr_comments_to_vet': nr_comments_to_vet, 'nr_author_replies_to_vet': nr_author_replies_to_vet, 'nr_reports_to_vet': nr_reports_to_vet, 'nr_submissions_to_process': nr_submissions_to_process }
        return render(request, 'scipost/personal_page.html', context)
    else:
        return render(request, 'scipost/login.html')




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
        return render(request, 'scipost/request_commentary.html', {'form': form})
    else: # user is not authenticated:
        return render(request, 'scipost/login.html')

def request_commentary_ack(request):
    return render(request, 'scipost/request_commentary_ack.html')

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
    return render(request, 'scipost/commentaries.html', context)

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
            return HttpResponseRedirect(reverse('scipost:comment_submission_ack'))
    else:
        form = CommentForm()

    comment_rating_form = CommentRatingForm()
    commentary_rating_form = CommentaryRatingForm()
    try:
        author_replies = AuthorReply.objects.filter(commentary=commentary)
    except AuthorReply.DoesNotExist:
        author_replies = ()
    context = {'commentary': commentary, 'comments': comments.filter(status__gte=1).order_by('date_submitted'), 'author_replies': author_replies, 'form': form, 'commentary_rating_form': commentary_rating_form, 'comment_rating_form': comment_rating_form}
    return render(request, 'scipost/commentary_detail.html', context)

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
            return HttpResponseRedirect(reverse('scipost:vote_on_commentary_ack'))

    return render(request, 'scipost/vote_on_commentary_ack.html')
            
def vote_on_commentary_ack(request):
    context = {}
    return render(request, 'scipost/vote_on_commentary_ack.html', context)


@csrf_protect
def comment_submission_ack(request):
    return render(request, 'scipost/comment_submission_ack.html')

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
            return HttpResponseRedirect(reverse('scipost:vote_on_comment_ack'))

#    commentary = Commentary(pk=commentary_id)
#    comments = commentary.comment_set.all()
#    form = CommentForm()
#    comment_rating_form = CommentRatingForm()
    
#    context = {'commentary': commentary, 'comments': comments.order_by('date_submitted'), 'form': form, 'comment_rating_form': comment_rating_form}
#    return render(request, 'scipost/commentary_detail.html', context)
    return render(request, 'scipost/vote_on_comment_ack.html')

@csrf_protect            
def vote_on_comment_ack(request):
#    context = {'commentary_id': request.session['commentary_id']}
    context = {}
    return render(request, 'scipost/vote_on_comment_ack.html', context)


@csrf_protect
def reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            newcomment = Comment (
                commentary = comment.commentary, # one of commentary or submission will be not Null
                submission = comment.submission,
                in_reply_to = comment,
                author = Contributor.objects.get(user=request.user),
                comment_text = form.cleaned_data['comment_text'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
#            request.session['commentary_id'] = comment.commentary.id
            return HttpResponseRedirect(reverse('scipost:comment_submission_ack'))
    else:
        form = CommentForm()

    context = {'comment': comment, 'form': form}
    return render(request, 'scipost/reply_to_comment.html', context)

@csrf_protect
def author_reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == 'POST':
        form = AuthorReplyForm(request.POST)
        if form.is_valid():
            newreply = AuthorReply (
                commentary = comment.commentary, # one of commentary or submission will be not Null
                submission = comment.submission,
                in_reply_to_comment = comment,
                author = Contributor.objects.get(user=request.user),
                reply_text = form.cleaned_data['reply_text'],
                date_submitted = timezone.now(),
                )
            newreply.save()
#            request.session['commentary_id'] = comment.commentary.id
            return HttpResponseRedirect(reverse('scipost:comment_submission_ack'))
    else:
        form = AuthorReplyForm()

    context = {'comment': comment, 'form': form}
    return render(request, 'scipost/author_reply_to_comment.html', context)

@csrf_protect
def vet_author_replies(request):
    contributor = Contributor.objects.get(user=request.user)
    replies_to_vet = AuthorReply.objects.filter(status=0)
    form = VetAuthorReplyForm()
    context = {'contributor': contributor, 'replies_to_vet': replies_to_vet, 'form': form }
    return(render(request, 'scipost/vet_author_replies.html', context))

@csrf_protect
def vet_author_reply_ack(request, reply_id):
    if request.method == 'POST':
        form = VetAuthorReplyForm(request.POST)
        reply = AuthorReply.objects.get(pk=reply_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the reply as is
                reply.status = 1
                reply.save()
            elif form.cleaned_data['action_option'] == '2':
                # the reply is simply rejected
                reply.status = form.cleaned_data['refusal_reason']
                reply.save()
                # email author

    context = {}
    return render(request, 'scipost/vet_author_reply_ack.html', context)



@csrf_protect
def vet_commentary_requests(request):
    contributor = Contributor.objects.get(user=request.user)
    commentary_requests_to_vet = Commentary.objects.filter(vetted=False)
    form = VetCommentaryForm()
    context = {'contributor': contributor, 'commentary_requests_to_vet': commentary_requests_to_vet, 'form': form }
    return render(request, 'scipost/vet_commentary_requests.html', context)

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
                return render(request, 'scipost/request_commentary.html', context)
            elif form.cleaned_data['action_option'] == '2':
                # the commentary request is simply rejected
                # email Contributor about it...
                commentary.delete()

#    context = {'option': form.cleaned_data['action_option'], 'reason': form.cleaned_data['refusal_reason'] }
    context = { }
    return render(request, 'scipost/vet_commentary_request_ack.html', context)


@csrf_protect
def vet_submitted_comments(request):
    contributor = Contributor.objects.get(user=request.user)
    submitted_comments_to_vet = Comment.objects.filter(status=0)
    form = VetCommentForm()
    context = {'contributor': contributor, 'submitted_comments_to_vet': submitted_comments_to_vet, 'form': form }
    return(render(request, 'scipost/vet_submitted_comments.html', context))

@csrf_protect
def vet_submitted_comment_ack(request, comment_id):
    if request.method == 'POST':
        form = VetCommentForm(request.POST)
        comment = Comment.objects.get(pk=comment_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the comment as is
                comment.status = 1
                comment.save()
            elif form.cleaned_data['action_option'] == '2':
                # the comment request is simply rejected
                comment.status = form.cleaned_data['refusal_reason']
                comment.save()

    context = {}
    return render(request, 'scipost/vet_submitted_comment_ack.html', context)


# SUBMISSIONS:

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
            return HttpResponseRedirect(reverse('scipost:submit_manuscript_ack'))
    else:
        form = SubmissionForm()
    return render(request, 'scipost/submit_manuscript.html', {'form': form})

@csrf_protect
def submit_manuscript_ack(request):
    return render(request, 'scipost/submit_manuscript_ack.html')

@csrf_protect
def process_new_submissions(request):
    submissions_to_process = Submission.objects.filter(status='0')
    form = ProcessSubmissionForm()
    context = {'submissions_to_process': submissions_to_process, 'form': form }
    return render(request, 'scipost/process_new_submissions.html', context)

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
    return render(request, 'scipost/process_new_submission_ack.html', context)

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
    return render(request, 'scipost/submissions.html', context)


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
            return HttpResponseRedirect(reverse('scipost:comment_submission_ack'))
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
    return render(request, 'scipost/submission_detail.html', context)

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
            return HttpResponseRedirect(reverse('scipost:vote_on_submission_ack'))

    return render(request, 'scipost/vote_on_submission_ack.html')
            
def vote_on_submission_ack(request):
    context = {}
    return render(request, 'scipost/vote_on_submission_ack.html', context)





###########
# Reports
###########

@csrf_protect
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
                recommendation = form.cleaned_data['recommendation'],
                date_submitted = timezone.now(),
                )
            newreport.save()
            author.nr_reports = Report.objects.filter(author=author).count()
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('scipost:submit_report_ack'))

    else:
        form = ReportForm()
    context = {'submission': submission, 'form': form }
    return render(request, 'scipost/submit_report.html', context)

@csrf_protect
def submit_report_ack(request):
#    submission_id = request.session['submission_id']
#    context = {'submission': Submission.objects.get(pk=submission_id) }
    context = {}
    return render(request, 'scipost/submit_report_ack.html', context)

@csrf_protect
def vet_submitted_reports(request):
    contributor = Contributor.objects.get(user=request.user)
    submitted_reports_to_vet = Report.objects.filter(status=0)
    form = VetReportForm()
    context = {'contributor': contributor, 'submitted_reports_to_vet': submitted_reports_to_vet, 'form': form }
    return(render(request, 'scipost/vet_submitted_reports.html', context))

@csrf_protect
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
    return render(request, 'scipost/vet_submitted_report_ack.html', context)

@csrf_protect
def author_reply_to_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == 'POST':
        form = AuthorReplyForm(request.POST)
        if form.is_valid():
            newreply = AuthorReply (
                submission = comment.submission,
                in_reply_to_report = report,
                author = Contributor.objects.get(user=request.user),
                reply_text = form.cleaned_data['reply_text'],
                date_submitted = timezone.now(),
                )
            newreply.save()
            return HttpResponseRedirect(reverse('scipost:comment_submission_ack'))
    else:
        form = AuthorReplyForm()

    context = {'report': report, 'form': form}
    return render(request, 'scipost/author_reply_to_report.html', context)



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
            return HttpResponseRedirect(reverse('scipost:vote_on_report_ack'))

    return render(request, 'scipost/vote_on_report_ack.html')
            
def vote_on_report_ack(request):
#    context = {'commentary_id': request.session['commentary_id']}
    context = {}
    return render(request, 'scipost/vote_on_report_ack.html', context)


############
# Journals 
############

@csrf_protect
def journals(request):
    return render(request, 'scipost/journals.html')


