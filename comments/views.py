import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
#from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from scipost.models import title_dict


def vet_submitted_comments(request):
    contributor = Contributor.objects.get(user=request.user)
    comment_to_vet = Comment.objects.filter(status=0).first() # only handle one at a time
    #if comment_to_vet is not None:
    form = VetCommentForm()
    context = {'contributor': contributor, 'comment_to_vet': comment_to_vet, 'form': form }
    return(render(request, 'comments/vet_submitted_comments.html', context))


def vet_submitted_comment_ack(request, comment_id):
    if request.method == 'POST':
        form = VetCommentForm(request.POST)
        comment = Comment.objects.get(pk=comment_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the comment as is
                comment.status = 1
                comment.save()
                email_text = 'Dear ' + title_dict[comment.author.title] + ' ' + comment.author.user.last_name + ', \n\nThe Comment you have submitted, concerning publication with title '
                if comment.commentary is not None:
                    email_text += comment.commentary.pub_title + ' by ' + comment.commentary.author_list
                elif comment.submission is not None:
                    email_text += comment.submission.title + ' by ' + comment.submission.author_list
                email_text += ', has been accepted and published online.' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Comment published', email_text, 'comments@scipost.org', [comment.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)
            elif form.cleaned_data['action_option'] == '2':
                # the comment request is simply rejected
                comment.status = form.cleaned_data['refusal_reason']
                comment.save()
                email_text = 'Dear ' + title_dict[comment.author.title] + ' ' + comment.author.user.last_name + ', \n\nThe Comment you have submitted, concerning publication with title '
                if comment.commentary is not None:
                    email_text += comment.commentary.pub_title + ' by ' + comment.commentary.author_list
                elif comment.submission is not None:
                    email_text += comment.submission.title + ' by ' + comment.submission.author_list
                email_text += ', has been rejected for the following reason:' + comment_refusal_dict[form.cleaned_data['refusal_reason']] + '.\n\nThank you for your contribution, \nThe SciPost Team.'
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost Comment rejected', email_text, 'comments@scipost.org', [comment.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)

    context = {}
    return render(request, 'comments/vet_submitted_comment_ack.html', context)


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
                is_rem = form.cleaned_data['is_rem'],
                is_que = form.cleaned_data['is_que'],
                is_ans = form.cleaned_data['is_ans'],
                is_obj = form.cleaned_data['is_obj'],
                is_rep = form.cleaned_data['is_rep'],
                is_val = form.cleaned_data['is_val'],
                is_lit = form.cleaned_data['is_lit'],
                is_sug = form.cleaned_data['is_sug'],
                comment_text = form.cleaned_data['comment_text'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
#            request.session['commentary_id'] = comment.commentary.id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    context = {'comment': comment, 'form': form}
    return render(request, 'comments/reply_to_comment.html', context)



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
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = AuthorReplyForm()

    context = {'comment': comment, 'form': form}
    return render(request, 'comments/author_reply_to_comment.html', context)



def author_reply_to_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == 'POST':
        form = AuthorReplyForm(request.POST)
        if form.is_valid():
            newreply = AuthorReply (
                submission = report.submission,
                in_reply_to_report = report,
                author = Contributor.objects.get(user=request.user),
                reply_text = form.cleaned_data['reply_text'],
                date_submitted = timezone.now(),
                )
            newreply.save()
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = AuthorReplyForm()

    context = {'report': report, 'form': form}
    return render(request, 'comments/author_reply_to_report.html', context)



def vet_author_replies(request):
    contributor = Contributor.objects.get(user=request.user)
    reply_to_vet = AuthorReply.objects.filter(status=0).first() # only handle one at a time
    #if reply_to_vet is not None:
    form = VetAuthorReplyForm()
    context = {'contributor': contributor, 'reply_to_vet': reply_to_vet, 'form': form }
    return(render(request, 'comments/vet_author_replies.html', context))
    #return render (request, 'comments/no_author_reply_to_vet.html')

#def no_author_reply_to_vet(request):
#    return render (request, 'comments/no_author_reply_to_vet.html')


def vet_author_reply_ack(request, reply_id):
    if request.method == 'POST':
        form = VetAuthorReplyForm(request.POST)
        reply = AuthorReply.objects.get(pk=reply_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the reply as is
                reply.status = 1
                reply.save()
                email_text = 'The Author Reply you have submitted, concerning publication with title '
                if reply.commentary is not None:
                    email_text += reply.commentary.pub_title + ' by ' + reply.commentary.author_list
                elif reply.submission is not None:
                    email_text += reply.submission.title + ' by ' + reply.submission.author_list
                email_text += ', has been accepted and published online.' + '\n\nThank you for your contribution, \nThe SciPost Team.'
                emailmessage = EmailMessage('SciPost Author Reply published', email_text, 'comments@scipost.org', [reply.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)
            elif form.cleaned_data['action_option'] == '2':
                # the reply is simply rejected
                reply.status = form.cleaned_data['refusal_reason']
                reply.save()
                email_text = 'The Author Reply you have submitted, concerning publication with title '
                if reply.commentary is not None:
                    email_text += reply.commentary.pub_title + ' by ' + reply.commentary.author_list
                elif reply.submission is not None:
                    email_text += reply.submission.title + ' by ' + reply.submission.author_list
                email_text += ', has been rejected for the following reason:' + form.cleaned_data['refusal_reason'] + '.\n\nThank you for your contribution, \nThe SciPost Team.'
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                emailmessage = EmailMessage('SciPost AuthorReply rejected', email_text, 'comments@scipost.org', [reply.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)

    context = {}
    return render(request, 'comments/vet_author_reply_ack.html', context)


