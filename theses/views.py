__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

from .models import ThesisLink
from .forms import RequestThesisLinkForm, ThesisLinkSearchForm, VetThesisLinkForm

from comments.forms import CommentForm
from scipost.mixins import PaginationMixin

import strings


################
# Theses
################

@method_decorator(login_required, name='dispatch')
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


class ThesisListView(PaginationMixin, ListView):
    model = ThesisLink
    form = ThesisLinkSearchForm
    paginate_by = 10

    def get_queryset(self):
        # Context is not saved to View object by default
        self.pre_context = self.kwargs

        # Queryset for browsing
        if self.kwargs.get('browse', False):
            return (self.model.objects.vetted()
                    .filter(latest_activity__gte=timezone.now() + datetime.timedelta(
                        weeks=-int(self.kwargs['nrweeksback'])))
                    .order_by('-latest_activity'))

        # Queryset for searchform is processed by managers
        form = self.form(self.request.GET)
        if form.is_valid() and form.has_changed():
            return self.model.objects.search_results(form).order_by('-latest_activity')
        self.pre_context['recent'] = True
        return self.model.objects.vetted().order_by('-latest_activity')

    def get_context_data(self, **kwargs):
        # Update the context data from `get_queryset`
        context = super().get_context_data(**kwargs)
        context.update(self.pre_context)

        # Search form added to context
        context['form'] = self.form(initial=self.request.GET)

        return context


def thesis_detail(request, thesislink_id):
    thesislink = get_object_or_404(ThesisLink, pk=thesislink_id)
    form = CommentForm()

    context = {'thesislink': thesislink, 'form': form}
    return render(request, 'theses/thesis_detail.html', context)
