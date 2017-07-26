from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import transaction

from guardian.shortcuts import assign_perm, get_objects_for_user
import strings

from .models import Comment
from .forms import CommentForm, VetCommentForm

from theses.models import ThesisLink
from submissions.utils import SubmissionUtils
from submissions.models import Submission, Report
from commentaries.models import Commentary


@permission_required('scipost.can_submit_comments', raise_exception=True)
def new_comment(request, **kwargs):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        object_id = int(kwargs["object_id"])
        type_of_object = kwargs["type_of_object"]

        new_comment = form.save(commit=False)
        new_comment.author = request.user.contributor

        if type_of_object == "thesislink":
            _object = get_object_or_404(ThesisLink.objects.open_for_commenting(), id=object_id)
            new_comment.thesislink = _object
            new_comment.save()
        elif type_of_object == "submission":
            _object = get_object_or_404(Submission.objects.open_for_commenting(), id=object_id)
            new_comment.submission = _object
            new_comment.save()
            _object.add_event_for_eic('A new comment has been added.')

            # Add permissions for EIC only, the Vetting-group already has it!
            assign_perm('comments.can_vet_comments', _object.editor_in_charge.user, new_comment)
        elif type_of_object == "commentary":
            _object = get_object_or_404(Commentary.objects.open_for_commenting(), id=object_id)
            new_comment.commentary = _object
            new_comment.save()

        messages.success(request, strings.acknowledge_submit_comment)
        return redirect(_object.get_absolute_url())


@permission_required('scipost.can_vet_comments', raise_exception=True)
def vet_submitted_comments_list(request):
    comments_to_vet = Comment.objects.awaiting_vetting().order_by('date_submitted')
    form = VetCommentForm()
    context = {'comments_to_vet': comments_to_vet, 'form': form}
    return(render(request, 'comments/vet_submitted_comments_list.html', context))


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
            # accept the comment as is
            comment.status = 1
            comment.vetted_by = request.user.contributor
            comment.save()

            comment.submission.add_event_for_eic('A Comment has been accepted.')
            comment.submission.add_event_for_author('A new Comment has been added.')

            email_text = ('Dear ' + comment.author.get_title_display() + ' '
                          + comment.author.user.last_name +
                          ', \n\nThe Comment you have submitted, '
                          'concerning publication with title ')
            if comment.commentary is not None:
                email_text += (comment.commentary.pub_title + ' by '
                               + comment.commentary.author_list
                               + ' at Commentary Page https://scipost.org/commentary/'
                               + comment.commentary.arxiv_or_DOI_string)
                comment.commentary.latest_activity = timezone.now()
                comment.commentary.save()
            elif comment.submission is not None:
                email_text += (comment.submission.title + ' by '
                               + comment.submission.author_list
                               + ' at Submission page https://scipost.org/submission/'
                               + comment.submission.arxiv_identifier_w_vn_nr)
                comment.submission.latest_activity = timezone.now()
                comment.submission.save()
                if not comment.is_author_reply:
                    SubmissionUtils.load({'submission': comment.submission})
                    SubmissionUtils.send_author_comment_received_email()
            elif comment.thesislink is not None:
                email_text += (comment.thesislink.title + ' by ' + comment.thesislink.author +
                               ' at Thesis Link https://scipost.org/thesis/'
                               + str(comment.thesislink.id))
                comment.thesislink.latest_activity = timezone.now()
                comment.thesislink.save()
            email_text += (', has been accepted and published online.' +
                           '\n\nWe copy it below for your convenience.' +
                           '\n\nThank you for your contribution, \nThe SciPost Team.' +
                           '\n\n' + comment.comment_text)
            emailmessage = EmailMessage('SciPost Comment published', email_text,
                                        'comments@scipost.org',
                                        [comment.author.user.email],
                                        ['comments@scipost.org'],
                                        reply_to=['comments@scipost.org'])
            emailmessage.send(fail_silently=False)
        elif form.cleaned_data['action_option'] == '2':
            # the comment request is simply rejected
            comment.status = int(form.cleaned_data['refusal_reason'])
            if comment.status == 0:
                comment.status == -1
            comment.save()

            comment.submission.add_event_for_eic('A Comment has been rejected.')

            email_text = ('Dear ' + comment.author.get_title_display() + ' '
                          + comment.author.user.last_name
                          + ', \n\nThe Comment you have submitted, '
                          'concerning publication with title ')
            if comment.commentary is not None:
                email_text += comment.commentary.pub_title + ' by ' +\
                                                        comment.commentary.author_list
            elif comment.submission is not None:
                email_text += comment.submission.title + ' by ' +\
                                                        comment.submission.author_list
            elif comment.thesislink is not None:
                email_text += comment.thesislink.title + ' by ' + comment.thesislink.author
            email_text += (', has been rejected for the following reason: '
                           + comment.get_status_display() + '.' +
                           '\n\nWe copy it below for your convenience.' +
                           '\n\nThank you for your contribution, \n\nThe SciPost Team.')
            if form.cleaned_data['email_response_field']:
                email_text += '\n\nFurther explanations: ' +\
                                                    form.cleaned_data['email_response_field']
            email_text += '\n\n' + comment.comment_text
            emailmessage = EmailMessage('SciPost Comment rejected', email_text,
                                        'comments@scipost.org',
                                        [comment.author.user.email],
                                        ['comments@scipost.org'],
                                        reply_to=['comments@scipost.org'])
            emailmessage.send(fail_silently=False)

        messages.success(request, 'Submitted Comment vetted.')
        if comment.submission and comment.submission.editor_in_charge == request.user.contributor:
            # Redirect a EIC back to the Editorial Page!
            return redirect(reverse('submissions:editorial_page',
                                    args=(comment.submission.arxiv_identifier_w_vn_nr,)))
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
    is_author = False
    if comment.submission and not is_author:
        is_author = comment.submission.authors.filter(id=request.user.contributor.id).exists()
    elif comment.commentary and not is_author:
        is_author = comment.commentary.authors.filter(id=request.user.contributor.id).exists()
    elif comment.thesislink and not is_author:
        is_author = comment.thesislink.author == request.user.contributor

    form = CommentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        newcomment = form.save(commit=False)
        # Either one of commentary, submission or thesislink will be not Null
        newcomment.commentary = comment.commentary
        newcomment.submission = comment.submission
        newcomment.thesislink = comment.thesislink
        newcomment.is_author_reply = is_author
        newcomment.in_reply_to_comment = comment
        newcomment.author = request.user.contributor
        newcomment.save()

        messages.success(request, '<h3>Thank you for contributing a Reply</h3>'
                                  'It will soon be vetted by an Editor.')

        if newcomment.submission:
            return redirect(newcomment.submission.get_absolute_url())
        elif newcomment.commentary:
            return redirect(newcomment.commentary.get_absolute_url())
        elif newcomment.thesislink:
            return redirect(newcomment.thesislink.get_absolute_url())
        return redirect(reverse('scipost:index'))

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
        newcomment.submission = report.submission
        newcomment.is_author_reply = is_author
        newcomment.in_reply_to_report = report
        newcomment.author = request.user.contributor
        newcomment.save()

        messages.success(request, '<h3>Thank you for contributing a Reply</h3>'
                                  'It will soon be vetted by an Editor.')
        return redirect(newcomment.submission.get_absolute_url())

    context = {'report': report, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_report.html', context)


@permission_required('scipost.can_express_opinion_on_comments', raise_exception=True)
def express_opinion(request, comment_id, opinion):
    # A contributor has expressed an opinion on a comment
    contributor = request.user.contributor
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.update_opinions(contributor.id, opinion)
    if comment.submission is not None:
        return HttpResponseRedirect('/submission/' + comment.submission.arxiv_identifier_w_vn_nr +
                                    '/#comment_id' + str(comment.id))
    if comment.commentary is not None:
        return HttpResponseRedirect('/commentary/' + str(comment.commentary.arxiv_or_DOI_string) +
                                    '/#comment_id' + str(comment.id))
    if comment.thesislink is not None:
        return HttpResponseRedirect('/thesis/' + str(comment.thesislink.id) +
                                    '/#comment_id' + str(comment.id))
    else:
        # will never call this
        return(render(request, 'scipost/index.html'))
