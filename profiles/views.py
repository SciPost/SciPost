__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin

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
        if self.kwargs.get('discipline', None):
            queryset = queryset.filter(discipline=self.kwargs['discipline'].lower())
            if self.kwargs.get('expertise', None):
                queryset = queryset.filter(expertises__contains=[self.kwargs['expertise']])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_areas'] = SCIPOST_SUBJECT_AREAS
        return context
