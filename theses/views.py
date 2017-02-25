import datetime

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

from .models import ThesisLink
from .forms import RequestThesisLinkForm, ThesisLinkSearchForm, VetThesisLinkForm

from comments.models import Comment
from comments.forms import CommentForm
from scipost.forms import TITLE_CHOICES
from scipost.models import Contributor
import strings

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

    def get_form_kwargs(self):
        kwargs = super(RequestThesisLink, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


@method_decorator(permission_required(
    'scipost.can_vet_thesislink_requests', raise_exception=True), name='dispatch')
class UnvettedThesisLinks(ListView):
    model = ThesisLink
    template_name = 'theses/unvetted_thesislinks.html'
    context_object_name = 'thesislinks'
    queryset = ThesisLink.objects.filter(vetted=False)


@method_decorator(permission_required(
    'scipost.can_vet_thesislink_requests', raise_exception=True), name='dispatch')
class VetThesisLink(UpdateView):
    model = ThesisLink
    form_class = VetThesisLinkForm
    template_name = "theses/vet_thesislink.html"
    success_url = reverse_lazy('theses:unvetted_thesislinks')

    def form_valid(self, form):
        # I totally override the form_valid method. I do not call super.
        # This is because, by default, an UpdateView saves the object as instance,
        # which it builds from the form data. So, the changes (by whom the thesis link was
        # vetted, etc.) would be lost. Instead, we need the form to save with commit=False,
        # then modify the vetting fields, and then save.

        # Builds model that reflects changes made during update. Does not yet save.
        self.object = form.save(commit=False)
        # Process vetting actions (object already gets saved.)
        form.vet_request(self.object, self.request.user)
        # Save again.
        self.object.save()

        messages.add_message(
            self.request, messages.SUCCESS,
            strings.acknowledge_vet_thesis_link)
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super(VetThesisLink, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def theses(request):
    form = ThesisLinkSearchForm(request.GET)
    if form.is_valid() and form.has_changed():
        search_results = ThesisLink.objects.search_results(form)
        recent_theses = []
    else:
        recent_theses = ThesisLink.objects.latest(5)
        search_results = []

    context = {
        'form': form, 'search_results': search_results,
        'recent_theses': recent_theses
    }
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
    form = CommentForm()
    try:
        author_replies = Comment.objects.filter(thesislink=thesislink, is_author_reply=True)
    except Comment.DoesNotExist:
        author_replies = ()
    # TODO: make manager for horribly obfuscating 'status__gte=1'
    context = {'thesislink': thesislink,
               'comments': comments.filter(status__gte=1).order_by('date_submitted'),
               'author_replies': author_replies, 'form': form}
    return render(request, 'theses/thesis_detail.html', context)
