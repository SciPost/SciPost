from django.contrib.auth.decorators import permission_required, login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect

from guardian.shortcuts import get_objects_for_user
import strings

from .constants import EXTENTIONS_IMAGES, EXTENTIONS_PDF
from .models import Comment
from .forms import CommentForm, VetCommentForm
from .utils import CommentUtils, validate_file_extention

from theses.models import ThesisLink
from submissions.utils import SubmissionUtils
from submissions.models import Submission, Report
from commentaries.models import Commentary


@login_required
@permission_required('scipost.can_submit_comments', raise_exception=True)
def new_comment(request, **kwargs):
    form = CommentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        object_id = int(kwargs["object_id"])
        type_of_object = kwargs["type_of_object"]

        if type_of_object == "thesislink":
            _object = get_object_or_404(ThesisLink.objects.open_for_commenting(), id=object_id)
        elif type_of_object == "submission":
            _object = get_object_or_404(Submission.objects.open_for_commenting(), id=object_id)
            _object.add_event_for_eic('A new comment has been added.')
        elif type_of_object == "commentary":
            _object = get_object_or_404(Commentary.objects.open_for_commenting(), id=object_id)

        new_comment = form.save(commit=False)
        new_comment.author = request.user.contributor
        new_comment.content_object = _object
        new_comment.save()
        new_comment.grant_permissions()

        messages.success(request, strings.acknowledge_submit_comment)
        return redirect(_object.get_absolute_url())
    context = {'form': form}
    return(render(request, 'comments/add_comment.html', context))


@permission_required('scipost.can_vet_comments', raise_exception=True)
def vet_submitted_comments_list(request):
    comments_to_vet = Comment.objects.awaiting_vetting().order_by('date_submitted')
    form = VetCommentForm()
    context = {'comments_to_vet': comments_to_vet, 'form': form}
    return(render(request, 'comments/vet_submitted_comments.html', context))


@login_required
@transaction.atomic
def vet_submitted_comment(request, comment_id):
    # Method `get_objects_for_user` gets all Comments that are assigned to the user
    # or *all* comments if user has the `scipost.can_vet_comments` permission.
    comment = get_object_or_404((get_objects_for_user(request.user, 'comments.can_vet_comments')
                                 .awaiting_vetting()),
                                id=comment_id)
    form = VetCommentForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data['action_option'] == '1':
            # Accept the comment as is
            comment.status = 1
            comment.vetted_by = request.user.contributor
            comment.save()

            # Send emails
            CommentUtils.load({'comment': comment})
            CommentUtils.email_comment_vet_accepted_to_author()

            # Update `latest_activity` fields
            content_object = comment.content_object
            content_object.latest_activity = timezone.now()
            content_object.save()

            if isinstance(content_object, Submission):
                # Add events to Submission and send mail to author of the Submission
                content_object.add_event_for_eic('A Comment has been accepted.')
                content_object.add_event_for_author('A new Comment has been added.')
                if not comment.is_author_reply:
                    SubmissionUtils.load({'submission': content_object})
                    SubmissionUtils.send_author_comment_received_email()
            elif isinstance(content_object, Report):
                # Add events to related Submission and send mail to author of the Submission
                content_object.submission.add_event_for_eic('A Comment has been accepted.')
                content_object.submission.add_event_for_author('A new Comment has been added.')
                if not comment.is_author_reply:
                    SubmissionUtils.load({'submission': content_object.submission})
                    SubmissionUtils.send_author_comment_received_email()

        elif form.cleaned_data['action_option'] == '2':
            # The comment request is simply rejected
            comment.status = int(form.cleaned_data['refusal_reason'])
            if comment.status == 0:
                comment.status = -1  # Why's this here??
            comment.save()

            # Send emails
            CommentUtils.load({'comment': comment})
            CommentUtils.email_comment_vet_rejected_to_author(
                email_response=form.cleaned_data['email_response_field'])

            if isinstance(comment.content_object, Submission):
                # Add event if commented to Submission
                comment.content_object.add_event_for_eic('A Comment has been rejected.')
            elif isinstance(comment.content_object, Report):
                comment.content_object.submission.add_event_for_eic('A Comment has been rejected.')

        messages.success(request, 'Submitted Comment vetted.')
        if isinstance(comment.content_object, Submission):
            submission = comment.content_object
            if submission.editor_in_charge == request.user.contributor:
                # Redirect a EIC back to the Editorial Page!
                return redirect(reverse('submissions:editorial_page',
                                        args=(submission.arxiv_identifier_w_vn_nr,)))
        elif isinstance(comment.content_object, Report):
            submission = comment.content_object.submission
            if submission.editor_in_charge == request.user.contributor:
                # Redirect a EIC back to the Editorial Page!
                return redirect(reverse('submissions:editorial_page',
                                        args=(submission.arxiv_identifier_w_vn_nr,)))
        elif request.user.has_perm('scipost.can_vet_comments'):
            # Redirect vetters back to check for other unvetted comments!
            return redirect(reverse('comments:vet_submitted_comments_list'))
        return redirect(comment.get_absolute_url())

    context = {
        'comment': comment,
        'form': form
    }
    return(render(request, 'comments/vet_submitted_comment.html', context))


@permission_required('scipost.can_submit_comments', raise_exception=True)
def reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    # Verify if this is from an author:
    related_object = comment.content_object
    if isinstance(related_object, Submission) or isinstance(related_object, Commentary):
        is_author = related_object.authors.filter(id=request.user.contributor.id).exists()
    elif isinstance(related_object, Report):
        is_author = related_object.submission.authors.filter(
            id=request.user.contributor.id).exists()
    elif isinstance(related_object, ThesisLink):
        # ThesisLink
        is_author = related_object.author == request.user.contributor
    else:
        # No idea what this could be, but just to be sure
        is_author = related_object.author == request.user.contributor

    form = CommentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        newcomment = form.save(commit=False)
        newcomment.content_object = comment
        newcomment.is_author_reply = is_author
        newcomment.author = request.user.contributor
        newcomment.save()
        newcomment.grant_permissions()

        messages.success(request, '<h3>Thank you for contributing a Reply</h3>'
                                  'It will soon be vetted by an Editor.')
        return redirect(newcomment.content_object.get_absolute_url())

    context = {'comment': comment, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_comment.html', context)


@permission_required('scipost.can_submit_comments', raise_exception=True)
def reply_to_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    # Verify if this is from an author:
    is_author = report.submission.authors.filter(user=request.user).exists()

    form = CommentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        newcomment = form.save(commit=False)
        newcomment.content_object = report
        newcomment.is_author_reply = is_author
        newcomment.author = request.user.contributor
        newcomment.save()
        newcomment.grant_permissions()

        messages.success(request, '<h3>Thank you for contributing a Reply</h3>'
                                  'It will soon be vetted by an Editor.')
        return redirect(newcomment.content_object.get_absolute_url())

    context = {'report': report, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_report.html', context)


@permission_required('scipost.can_express_opinion_on_comments', raise_exception=True)
def express_opinion(request, comment_id, opinion):
    # A contributor has expressed an opinion on a comment
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.update_opinions(request.user.contributor.id, opinion)
    return redirect(comment.get_absolute_url())


def attachment(request, comment_id):
    """
    Open/read attachment of Comment if available.
    """
    comment = get_object_or_404(Comment.objects.exclude(file_attachment=''), pk=comment_id)
    if validate_file_extention(comment.file_attachment, EXTENTIONS_IMAGES):
        content_type = 'image/jpeg'
    elif validate_file_extention(comment.file_attachment, EXTENTIONS_PDF):
        content_type = 'application/pdf'
    else:
        raise Http404

    response = HttpResponse(comment.file_attachment.read(), content_type=content_type)
    filename = 'comment-attachment-%s' % comment.file_attachment.name
    response['Content-Disposition'] = ('filename=' + filename)
    return response
