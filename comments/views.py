__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import time
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
from .utils import validate_file_extention

from commentaries.models import Commentary
from mails.utils import DirectMailUtil
from submissions.models import Submission, Report
from theses.models import ThesisLink


@login_required
@permission_required('scipost.can_submit_comments', raise_exception=True)
def new_comment(request, **kwargs):
    """Form view to submit new Comment."""
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

        # Mails
        mail_sender = DirectMailUtil(
            'commenters/inform_commenter_comment_received', comment=new_comment)
        mail_sender.send_mail()

        if isinstance(new_comment.core_content_object, Submission):
            mail_sender = DirectMailUtil('eic/inform_eic_comment_received', comment=new_comment)
            mail_sender.send_mail()

        messages.success(request, strings.acknowledge_submit_comment)
        return redirect(_object.get_absolute_url())
    context = {'form': form}
    return(render(request, 'comments/add_comment.html', context))


@permission_required('scipost.can_vet_comments', raise_exception=True)
def vet_submitted_comments_list(request):
    """Replace by a list page instead?"""
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
            Comment.objects.filter(id=comment_id).update(status=1,
                                                         vetted_by=request.user.contributor)
            comment.refresh_from_db()

            # Update `latest_activity` fields
            content_object = comment.content_object
            if hasattr(content_object, 'latest_activity'):
                content_object.__class__.objects.filter(id=content_object.id).update(
                    latest_activity=timezone.now())
                content_object.refresh_from_db()

            if isinstance(content_object, Submission):
                # Add events to Submission and send mail to author of the Submission
                content_object.add_event_for_eic('A Comment has been accepted.')
                content_object.add_event_for_author('A new Comment has been added.')
                if not comment.is_author_reply:
                    mail_sender = DirectMailUtil(
                        'authors/inform_authors_comment_received', submission=content_object)
                    mail_sender.send_mail()
            elif isinstance(content_object, Report):
                # Add events to related Submission and send mail to author of the Submission
                content_object.submission.add_event_for_eic('A Comment has been accepted.')
                content_object.submission.add_event_for_author('A new Comment has been added.')
                if comment.is_author_reply:
                    # Email Report author: Submission authors have replied
                    mail_sender = DirectMailUtil(
                        'referees/inform_referee_authors_replied_to_report',
                        report=content_object)
                    mail_sender.send_mail()
                else: # this is a Comment on the Report from another Contributor
                    # Email Report author: Contributor has commented the Report
                    mail_sender = DirectMailUtil(
                        'referees/inform_referee_contributor_commented_report',
                        report=content_object)
                    mail_sender.send_mail()
                    # Email submission authors: Contributor has commented the Report
                    mail_sender = DirectMailUtil(
                        'authors/inform_authors_contributor_commented_report',
                        report=content_object)
                    mail_sender.send_mail()

            # In all cases, email the comment author
            mail_sender = DirectMailUtil(
                'commenters/inform_commenter_comment_vetted', comment=comment)
            mail_sender.send_mail()

        elif form.cleaned_data['action_option'] == '2':
            # The comment request is simply rejected
            Comment.objects.filter(id=comment.id).update(
                status=int(form.cleaned_data['refusal_reason']))
            comment.refresh_from_db()

            # Send emails
            mail_sender = DirectMailUtil(
                'commenters/inform_commenter_comment_rejected',
                comment=comment,
                email_response=form.cleaned_data['email_response_field']) # TODO: needs kwargs to mail template
            mail_sender.send_mail()


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
                                        args=(submission.preprint.identifier_w_vn_nr,)))
        elif isinstance(comment.content_object, Report):
            submission = comment.content_object.submission
            if submission.editor_in_charge == request.user.contributor:
                # Redirect a EIC back to the Editorial Page!
                return redirect(reverse('submissions:editorial_page',
                                        args=(submission.preprint.identifier_w_vn_nr,)))
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
@transaction.atomic
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

        mail_sender = DirectMailUtil(
            'commenters/inform_commenter_comment_received', comment=newcomment)
        mail_sender.send_mail()

        if isinstance(newcomment.core_content_object, Submission):
            mail_sender = DirectMailUtil('eic/inform_eic_comment_received', comment=newcomment)
            mail_sender.send_mail()

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

    form = CommentForm(request.POST or None, request.FILES or None, is_report_comment=True)
    if form.is_valid():
        newcomment = form.save(commit=False)
        newcomment.content_object = report
        newcomment.is_author_reply = is_author
        newcomment.author = request.user.contributor
        newcomment.save()
        newcomment.grant_permissions()

        mail_sender = DirectMailUtil('eic/inform_eic_comment_received', comment=newcomment)
        mail_sender.send_mail()

        mail_sender = DirectMailUtil(
            'commenters/inform_commenter_comment_received', comment=newcomment)
        mail_sender.send_mail()

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
