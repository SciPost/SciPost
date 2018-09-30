__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin
from scipost.models import Contributor

from .models import Profile
from .forms import ProfileForm


class ProfileCreateView(PermissionsMixin, CreateView):
    """
    Formview to create a new Profile.
    """
    permission_required = 'scipost.can_create_profiles'
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profiles:profiles')

    def get_initial(self):
        """
        Provide initial data based on kwargs.
        The data can come from a Contributor, Invitation, UnregisteredAuthor, ...
        """
        initial = super().get_initial()
        from_type = self.kwargs.get('from_type', None)
        pk = self.kwargs.get('pk', None)
        print(from_type)
        print(pk)
        if pk:
            pk = int(pk)
            if from_type == 'contributor':
                contributor = get_object_or_404(Contributor, pk=pk)
                initial['title'] = contributor.title
                initial['first_name'] = contributor.user.first_name
                initial['last_name'] = contributor.user.last_name
                initial['email'] = contributor.user.email
                initial['discipline'] = contributor.discipline
                initial['expertises'] = contributor.expertises
                initial['orcid_id'] = contributor.orcid_id
                initial['webpage'] = contributor.personalwebpage
                initial['accepts_SciPost_emails'] = contributor.accepts_SciPost_emails
        return initial


class ProfileUpdateView(PermissionsMixin, UpdateView):
    """
    Formview to update a Profile.
    """
    permission_required = 'scipost.can_create_profiles'
    model = Profile
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profiles:profiles')


class ProfileDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Profile.
    """
    permission_required = 'scipost.can_create_profiles'
    model = Profile
    success_url = reverse_lazy('profiles:profiles')


class ProfileListView(PermissionsMixin, ListView):
    """
    List Profile object instances.
    """
    permission_required = 'scipost.can_view_profiles'
    model = Profile
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of Profiles using optional GET data.
        """
        queryset = Profile.objects.all()
        if self.request.GET.get('discipline', None):
            queryset = queryset.filter(discipline=self.request.GET['discipline'].lower())
            if self.request.GET.get('expertise', None):
                queryset = queryset.filter(expertises__contains=[self.request.GET['expertise']])
        if self.request.GET.get('contributor', None) == 'False':
            queryset = queryset.filter(contributor=None)
        elif self.request.GET.get('contributor', None) == 'True':
            queryset = queryset.exclude(contributor=None)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_areas'] = SCIPOST_SUBJECT_AREAS
        contributors_wo_profile = Contributor.objects.filter(profile=None)
        context['nr_contributors_wo_profile'] = contributors_wo_profile.count()
        context['next_contributor_wo_profile'] = random.choice(contributors_wo_profile)
        return context
