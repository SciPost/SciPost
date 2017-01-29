import datetime

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg
from django.views.generic.edit import CreateView, FormView
from django.utils.decorators import method_decorator

from .models import *
from .forms import *

from comments.models import Comment
from comments.forms import CommentForm
from scipost.forms import TITLE_CHOICES, AuthenticationForm


title_dict = dict(TITLE_CHOICES)  # Convert titles for use in emails

################
# Theses
################


@method_decorator(permission_required(
    'scipost.can_request_thesislinks', raise_exception=True), name='dispatch')
class RequestThesisLink(CreateView):
    form_class = RequestThesisLinkForm
    template_name = 'theses/request_thesislink.html'
    success_url = reverse_lazy('scipost:personal_page')

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             strings.acknowledge_request_thesis_link)
        return super(RequestThesisLink, self).form_valid(form)


@method_decorator(permission_required(
    'scipost.can_vet_thesislink_requests', raise_exception=True), name='dispatch')
class VetThesisLinkRequests(FormView):
    form_class = VetThesisLinkForm
    template_name = 'theses/vet_thesislink_requests.html'
    # TODO: not right yet
    success_url = reverse_lazy('theses:vet_thesislink_requests')

    def get_context_data(self, **kwargs):
        context = super(VetThesisLinkRequests, self).get_context_data(**kwargs)
        context['thesislink_to_vet'] = self.thesislink_to_vet()
        return context

    def thesislink_to_vet(self):
        return ThesisLink.objects.filter(vetted=False).first()

    def form_valid(self, form):
        form.vet_request(self.thesislink_to_vet())
        return super(VetThesisLinkRequests, self).form_valid(form)


# @permission_required('scipost.can_vet_thesislink_requests', raise_exception=True)
# def vet_thesislink_requests(request):
#     contributor = Contributor.objects.get(user=request.user)
#     thesislink_to_vet = ThesisLink.objects.filter(
#         vetted=False).first()  # only handle one at a time
#     form = VetThesisLinkForm()
#     context = {'contributor': contributor, 'thesislink_to_vet': thesislink_to_vet, 'form': form}
#     return render(request, 'theses/vet_thesislink_requests.html', context)


@permission_required('scipost.can_vet_thesislink_requests', raise_exception=True)
def vet_thesislink_request_ack(request, thesislink_id):
    if request.method == 'POST':
        form = VetThesisLinkForm(request.POST)
        thesislink = ThesisLink.objects.get(pk=thesislink_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                thesislink.vetted = True
                thesislink.vetted_by = Contributor.objects.get(user=request.user)
                thesislink.save()
                email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                              + thesislink.requested_by.user.last_name
                              + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                              + thesislink.title + ' by ' + thesislink.author
                              + ', has been activated at https://scipost.org/thesis/'
                              + str(thesislink.id) + '.'
                              + '\n\nThank you for your contribution, \nThe SciPost Team.')
                emailmessage = EmailMessage('SciPost Thesis Link activated', email_text,
                                            'SciPost Theses <theses@scipost.org>',
                                            [thesislink.requested_by.user.email],
                                            ['theses@scipost.org'],
                                            reply_to=['theses@scipost.org'])
                emailmessage.send(fail_silently=False)
            elif form.cleaned_data['action_option'] == '0':
                # re-edit the form starting from the data provided
                form2 = RequestThesisLinkForm(initial={'title': thesislink.pub_title,
                                                       'pub_ink': thesislink.pub_link,
                                                       'author': thesislink.author,
                                                       'institution': thesislink.institution,
                                                       'defense_date': thesislink.defense_date,
                                                       'abstract': thesislink.abstract})
                thesislink.delete()
                email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                              + thesislink.requested_by.user.last_name
                              + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                              + thesislink.title + ' by ' + thesislink.author_list
                              + ', has been activated '
                              '(with slight modifications to your submitted details) at '
                              'https://scipost.org/thesis/' + str(thesislink.id) + '.'
                              '\n\nThank you for your contribution, \nThe SciPost Team.')
                emailmessage = EmailMessage('SciPost Thesis Link activated', email_text,
                                            'SciPost Theses <theses@scipost.org>',
                                            [thesislink.requested_by.user.email],
                                            ['theses@scipost.org'],
                                            reply_to=['theses@scipost.org'])
                # Don't send email yet... only when option 1 has succeeded!
                # emailmessage.send(fail_silently=False)
                context = {'form': form2}
                return render(request, 'theses/request_thesislink.html', context)
            elif form.cleaned_data['action_option'] == '2':
                email_text = ('Dear ' + title_dict[thesislink.requested_by.title] + ' '
                              + thesislink.requested_by.user.last_name
                              + ', \n\nThe Thesis Link you have requested, concerning thesis with title '
                              + thesislink.title + ' by ' + thesislink.author
                              + ', has not been activated for the following reason: '
                              + form.cleaned_data['refusal_reason']
                              + '.\n\nThank you for your interest, \nThe SciPost Team.')
                if form.cleaned_data['justification']:
                    email_text += '\n\nFurther explanations: ' + \
                        form.cleaned_data['justification']
                emailmessage = EmailMessage('SciPost Thesis Link', email_text,
                                            'SciPost Theses <theses@scipost.org>',
                                            [thesislink.requested_by.user.email],
                                            ['theses@scipost.org'],
                                            reply_to=['theses@scipost.org'])
                emailmessage.send(fail_silently=False)
                thesislink.delete()

    context = {'ack_header': 'Thesis Link request vetted.',
               'followup_message': 'Return to the ',
               'followup_link': reverse('theses:vet_thesislink_requests'),
               'followup_link_label': 'Thesis Link requests page'}
    return render(request, 'scipost/acknowledgement.html', context)


def theses(request):
    if request.method == 'POST':
        form = ThesisLinkSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            thesislink_search_list = ThesisLink.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                supervisor__icontains=form.cleaned_data['supervisor'],
                vetted=True,
            )
            thesislink_search_list.order_by('-pub_date')
        else:
            thesislink_search_list = []

    else:
        form = ThesisLinkSearchForm()
        thesislink_search_list = []

    thesislink_recent_list = (ThesisLink.objects
                              .filter(vetted=True,
                                      latest_activity__gte=timezone.now() + datetime.timedelta(days=-7)))
    context = {'form': form, 'thesislink_search_list': thesislink_search_list,
               'thesislink_recent_list': thesislink_recent_list}
    return render(request, 'theses/theses.html', context)


def browse(request, discipline, nrweeksback):
    if request.method == 'POST':
        form = ThesisLinkSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            thesislink_search_list = ThesisLink.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                supervisor__icontains=form.cleaned_data['supervisor'],
                vetted=True,
            )
            thesislink_search_list.order_by('-pub_date')
        else:
            thesislink_search_list = []
        context = {'form': form, 'thesislink_search_list': thesislink_search_list}
        return HttpResponseRedirect(request, 'theses/theses.html', context)
    else:
        form = ThesisLinkSearchForm()
    thesislink_browse_list = (ThesisLink.objects.filter(
        vetted=True, discipline=discipline,
        latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback))))
    context = {'form': form, 'discipline': discipline,
               'nrweeksback': nrweeksback,
               'thesislink_browse_list': thesislink_browse_list}
    return render(request, 'theses/theses.html', context)


def thesis_detail(request, thesislink_id):
    thesislink = get_object_or_404(ThesisLink, pk=thesislink_id)
    comments = thesislink.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            new_comment = Comment(
                thesislink=thesislink,
                author=author,
                is_rem=form.cleaned_data['is_rem'],
                is_que=form.cleaned_data['is_que'],
                is_ans=form.cleaned_data['is_ans'],
                is_obj=form.cleaned_data['is_obj'],
                is_rep=form.cleaned_data['is_rep'],
                is_val=form.cleaned_data['is_val'],
                is_lit=form.cleaned_data['is_lit'],
                is_sug=form.cleaned_data['is_sug'],
                comment_text=form.cleaned_data['comment_text'],
                remarks_for_editors=form.cleaned_data['remarks_for_editors'],
                date_submitted=timezone.now(),
            )
            new_comment.save()
            author.nr_comments = Comment.objects.filter(author=author).count()
            author.save()
            context = {
                'ack_header': 'Thank you for contributing a Comment.',
                'ack_message': 'It will soon be vetted by an Editor.',
                'followup_message': 'Back to the ',
                'followup_link': reverse(
                    'theses:thesis',
                    kwargs={'thesislink_id': new_comment.thesislink.id}
                ),
                'followup_link_label': ' Thesis Link page you came from'
            }
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = CommentForm()

    try:
        author_replies = Comment.objects.filter(thesislink=thesislink, is_author_reply=True)
    except Comment.DoesNotExist:
        author_replies = ()
    context = {'thesislink': thesislink,
               'comments': comments.filter(status__gte=1).order_by('date_submitted'),
               'author_replies': author_replies, 'form': form}
    return render(request, 'theses/thesis_detail.html', context)
