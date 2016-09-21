import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group, Permission
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from scipost.models import title_dict
from submissions.utils import SubmissionUtils


@permission_required('scipost.can_vet_comments', raise_exception=True)
def vet_submitted_comments(request):
    contributor = Contributor.objects.get(user=request.user)
    comments_to_vet = Comment.objects.filter(status=0).order_by('date_submitted')
    form = VetCommentForm()
    context = {'contributor': contributor, 'comments_to_vet': comments_to_vet, 'form': form }
    return(render(request, 'comments/vet_submitted_comments.html', context))

@permission_required('scipost.can_vet_comments', raise_exception=True)
def vet_submitted_comment_ack(request, comment_id):
    if request.method == 'POST':
        form = VetCommentForm(request.POST)
        comment = Comment.objects.get(pk=comment_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the comment as is
                comment.status = 1
                comment.vetted_by = request.user.contributor
                comment.save()
                email_text = ('Dear ' + title_dict[comment.author.title] + ' ' 
                              + comment.author.user.last_name + 
                              ', \n\nThe Comment you have submitted, concerning publication with title ')
                if comment.commentary is not None:
                    email_text += (comment.commentary.pub_title + ' by ' + comment.commentary.author_list
                                   + ' at Commentary Page https://scipost.org/commentary/' 
                                   + comment.commentary.arxiv_or_DOI_string)
                    comment.commentary.latest_activity = timezone.now()
                    comment.commentary.save()
                elif comment.submission is not None:
                    email_text += (comment.submission.title + ' by ' + comment.submission.author_list 
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
                email_text = ('Dear ' + title_dict[comment.author.title] + ' ' 
                              + comment.author.user.last_name
                              + ', \n\nThe Comment you have submitted, '
                              'concerning publication with title ')
                if comment.commentary is not None:
                    email_text += comment.commentary.pub_title + ' by ' + comment.commentary.author_list
                elif comment.submission is not None:
                    email_text += comment.submission.title + ' by ' + comment.submission.author_list
                elif comment.thesislink is not None:
                    email_text += comment.thesislink.title + ' by ' + comment.thesislink.author
                email_text += (', has been rejected for the following reason: ' 
                               + comment_refusal_dict[comment.status] + '.' +
                               '\n\nWe copy it below for your convenience.' + 
                               '\n\nThank you for your contribution, \n\nThe SciPost Team.')
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                email_text += '\n\n' + comment.comment_text
                emailmessage = EmailMessage('SciPost Comment rejected', email_text,
                                            'comments@scipost.org', 
                                            [comment.author.user.email],
                                            ['comments@scipost.org'], 
                                            reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)

    #context = {}
    #return render(request, 'comments/vet_submitted_comment_ack.html', context)
    context = {'ack_header': 'Submitted Comment vetted.',
               'followup_message': 'Back to ',
               'followup_link': reverse('comments:vet_submitted_comments'),
               'followup_link_label': 'submitted Comments page'}
    return render(request, 'scipost/acknowledgement.html', context)


@permission_required('scipost.can_submit_comments', raise_exception=True)
def reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    # Verify if this is from an author:
    is_author = False
    if comment.submission is not None:
        if comment.submission.authors.filter(id=request.user.contributor.id).exists():
            is_author = True
    elif comment.commentary is not None:
        if comment.commentary.authors.filter(id=request.user.contributor.id).exists():
            is_author = True
    elif comment.thesislink is not None:
        if comment.thesislink.author == request.user.contributor:
            is_author = True

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            newcomment = Comment (
                commentary = comment.commentary, # one of commentary, submission or thesislink will be not Null
                submission = comment.submission,
                thesislink = comment.thesislink,
                is_author_reply = is_author,
                in_reply_to_comment = comment,
                author = Contributor.objects.get(user=request.user),
                is_rem = form.cleaned_data['is_rem'],
                is_que = form.cleaned_data['is_que'],
                is_ans = form.cleaned_data['is_ans'],
                is_obj = form.cleaned_data['is_obj'],
                is_rep = form.cleaned_data['is_rep'],
                is_cor = form.cleaned_data['is_cor'],
                is_val = form.cleaned_data['is_val'],
                is_lit = form.cleaned_data['is_lit'],
                is_sug = form.cleaned_data['is_sug'],
                comment_text = form.cleaned_data['comment_text'],
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
            #return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
            context = {'ack_header': 'Thank you for contributing a Reply.',
                       'ack_message': 'It will soon be vetted by an Editor.',
                       'followup_message': 'Back to the ',}
            if newcomment.submission is not None:
                context['followup_link'] = reverse(
                    'submissions:submission',
                    kwargs={'arxiv_identifier_w_vn_nr': newcomment.submission.arxiv_identifier_w_vn_nr}
                )
                context['followup_link_label'] = ' Submission page you came from'
            elif newcomment.commentary is not None:
                context['followup_link'] = reverse(
                    'commentaries:commentary',
                    kwargs={'arxiv_or_DOI_string': newcomment.commentary.arxiv_or_DOI_string})
                context['followup_link_label'] = ' Commentary page you came from'
            elif newcomment.thesislink is not None:
                context['followup_link'] = reverse(
                    'theses:thesis',
                    kwargs={'thesislink_id': newcomment.thesislink.id})
                context['followup_link_label'] = ' Thesis Link page you came from'
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = CommentForm()

    context = {'comment': comment, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_comment.html', context)


@permission_required('scipost.can_submit_comments', raise_exception=True)
def reply_to_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    # Verify if this is from an author:
    is_author = False
    if report.submission.authors.filter(id=request.user.contributor.id).exists():
        is_author = True
    if is_author and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            newcomment = Comment (
                submission = report.submission,
                is_author_reply = is_author,
                in_reply_to_report = report,
                author = Contributor.objects.get(user=request.user),
                is_rem = form.cleaned_data['is_rem'],
                is_que = form.cleaned_data['is_que'],
                is_ans = form.cleaned_data['is_ans'],
                is_obj = form.cleaned_data['is_obj'],
                is_rep = form.cleaned_data['is_rep'],
                is_cor = form.cleaned_data['is_cor'],
                is_val = form.cleaned_data['is_val'],
                is_lit = form.cleaned_data['is_lit'],
                is_sug = form.cleaned_data['is_sug'],
                comment_text = form.cleaned_data['comment_text'],
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
            #return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
            context = {'ack_header': 'Thank you for contributing a Reply.',
                       'ack_message': 'It will soon be vetted by an Editor.',
                       'followup_message': 'Back to the ',
                       'followup_link': reverse(
                           'submissions:submission',
                           kwargs={'arxiv_identifier_w_vn_nr': newcomment.submission.arxiv_identifier_w_vn_nr}
                       ),
                       'followup_link_label': ' Submission page you came from'
                   }
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = CommentForm()
    context = {'report': report, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_report.html', context)


@permission_required('scipost.can_express_opinion_on_comments', raise_exception=True)
def express_opinion(request, comment_id, opinion):
    # A contributor has expressed an opinion on a comment
    contributor = request.user.contributor
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.update_opinions (contributor.id, opinion)
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
