import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
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
    #comment_to_vet = Comment.objects.filter(status=0).first() # only handle one at a time
    comments_to_vet = Comment.objects.filter(status=0).order_by('date_submitted')
    form = VetCommentForm()
    context = {'contributor': contributor, 'comments_to_vet': comments_to_vet, 'form': form }
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
                email_text = ('Dear ' + title_dict[comment.author.title] + ' ' + comment.author.user.last_name + 
                              ', \n\nThe Comment you have submitted, concerning publication with title ')
                if comment.commentary is not None:
                    email_text += (comment.commentary.pub_title + ' by ' + comment.commentary.author_list +
                                   ' at Commentary Page https://scipost.org/commentary/' + comment.commentary.arxiv_or_DOI_string)
                    comment.commentary.latest_activity = timezone.now()
                    comment.commentary.save()
                elif comment.submission is not None:
                    email_text += (comment.submission.title + ' by ' + comment.submission.author_list +
                                   ' at Submission page https://scipost.org/submission/' + str(comment.submission.id))
                    comment.submission.latest_activity = timezone.now()
                    comment.submission.save()
                elif comment.thesislink is not None:
                    email_text += (comment.thesislink.title + ' by ' + comment.thesis.author +
                                   ' at Thesis Link https://scipost.org/thesis/' + str(comment.thesis.id))
                    comment.thesislink.latest_activity = timezone.now()
                    comment.thesislink.save()
                email_text += (', has been accepted and published online.' + 
                               '\n\nWe copy it below for your convenience.' + 
                               '\n\nThank you for your contribution, \nThe SciPost Team.' +
                               '\n\n' + comment.comment_text)
                emailmessage = EmailMessage('SciPost Comment published', email_text, 'comments@scipost.org', 
                                            [comment.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)
            elif form.cleaned_data['action_option'] == '2':
                # the comment request is simply rejected
                comment.status = int(form.cleaned_data['refusal_reason'])
                if comment.status == 0:
                    comment.status == -1
                comment.save()
                email_text = ('Dear ' + title_dict[comment.author.title] + ' ' + comment.author.user.last_name + 
                              ', \n\nThe Comment you have submitted, concerning publication with title ')
                if comment.commentary is not None:
                    email_text += comment.commentary.pub_title + ' by ' + comment.commentary.author_list
                elif comment.submission is not None:
                    email_text += comment.submission.title + ' by ' + comment.submission.author_list
                elif comment.thesislink is not None:
                    email_text += comment.thesislink.title + ' by ' + comment.thesislink.author
                email_text += (', has been rejected for the following reason: ' + comment_refusal_dict[comment.status] + '.' +
                               '\n\nWe copy it below for your convenience.' + 
                               '\n\nThank you for your contribution, \nThe SciPost Team.')
                if form.cleaned_data['email_response_field']:
                    email_text += '\n\nFurther explanations: ' + form.cleaned_data['email_response_field']
                email_text += '\n\n' + comment.comment_text
                emailmessage = EmailMessage('SciPost Comment rejected', email_text, 'comments@scipost.org', 
                                            [comment.author.user.email, 'comments@scipost.org'], reply_to=['comments@scipost.org'])
                emailmessage.send(fail_silently=False)

    context = {}
    return render(request, 'comments/vet_submitted_comment_ack.html', context)


def reply_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    # Verify if this is from an author:
    is_author = False
    if comment.submission is not None:
        if comment.submission.authors.filter(id=request.user.contributor.id).exists():
            is_author = True
    elif comment.commentary is not None:
        #if comment.commentary.authors__contains(request.user.contributor):
        #if request.user.contributor.comment_set.filter(id=comment_id).exists():
        if comment.commentary.authors.filter(id=request.user.contributor.id).exists():
            is_author = True

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            newcomment = Comment (
                commentary = comment.commentary, # one of commentary or submission will be not Null
                submission = comment.submission,
                is_author_reply = is_author,
                in_reply_to_comment = comment,
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
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
#            request.session['commentary_id'] = comment.commentary.id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    context = {'comment': comment, 'is_author': is_author, 'form': form}
    return render(request, 'comments/reply_to_comment.html', context)



def express_opinion(request, comment_id, opinion):
    # A contributor has expressed an opinion on a comment
    contributor = request.user.contributor
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.update_opinions (contributor.id, opinion)
    if comment.submission is not None:
        return HttpResponseRedirect('/submission/' + str(comment.submission.id) + '/#comment_id' + str(comment.id))
    if comment.commentary is not None:
        return HttpResponseRedirect('/commentary/' + str(comment.commentary.arxiv_or_DOI_string) + '/#comment_id' + str(comment.id))
    if comment.thesislink is not None:
        return HttpResponseRedirect('/thesis/' + str(comment.thesislink.id) + '/#comment_id' + str(comment.id))
    else: 
        # will never call this
        return(render(request, 'scipost/index.html'))
