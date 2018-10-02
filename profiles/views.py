__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin, PaginationMixin
from scipost.models import Contributor

from invitations.models import RegistrationInvitation
from submissions.models import RefereeInvitation

from .models import Profile, AlternativeEmail
from .forms import ProfileForm, AlternativeEmailForm, SearchTextForm



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

        if pk and from_type:
            pk = int(pk)
            if from_type == 'contributor':
                contributor = get_object_or_404(Contributor, pk=pk)
                initial.update({
                    'title': contributor.title,
                    'first_name': contributor.user.first_name,
                    'last_name': contributor.user.last_name,
                    'email': contributor.user.email,
                    'discipline': contributor.discipline,
                    'expertises': contributor.expertises,
                    'orcid_id': contributor.orcid_id,
                    'webpage': contributor.personalwebpage,
                    'accepts_SciPost_emails': contributor.accepts_SciPost_emails,
                })
            elif from_type == 'refereeinvitation':
                refinv = get_object_or_404(RefereeInvitation, pk=pk)
                initial.update({
                    'title': refinv.title,
                    'first_name': refinv.first_name,
                    'last_name': refinv.last_name,
                    'email': refinv.email_address,
                    'discipline': refinv.submission.discipline,
                    'expertises': refinv.submission.secondary_areas,
                })
            elif from_type == 'registrationinvitation':
                reginv = get_object_or_404(RegistrationInvitation, pk=pk)
                initial.update({
                    'title': reginv.title,
                    'first_name': reginv.first_name,
                    'last_name': reginv.last_name,
                    'email': reginv.email,
                })
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


class ProfileListView(PermissionsMixin, PaginationMixin, ListView):
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
        if self.request.GET.get('discipline'):
            queryset = queryset.filter(discipline=self.request.GET['discipline'].lower())
            if self.request.GET.get('expertise'):
                queryset = queryset.filter(expertises__contains=[self.request.GET['expertise']])
        if self.request.GET.get('contributor') == 'False':
            queryset = queryset.filter(contributor__isnull=True)
        elif self.request.GET.get('contributor') == 'True':
            queryset = queryset.filter(contributor__isnull=False)
        if self.request.GET.get('text'):
            queryset = queryset.filter(last_name__istartswith=self.request.GET['text'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contributors_wo_profile = Contributor.objects.filter(profile__isnull=True)
        refinv_wo_profile = RefereeInvitation.objects.filter(profile__isnull=True)
        reginv_wo_profile = RegistrationInvitation.objects.filter(profile__isnull=True)

        context.update({
            'subject_areas': SCIPOST_SUBJECT_AREAS,
            'searchform': SearchTextForm(initial={'text': self.request.GET.get('text')}),
            'contributors_w_duplicate_email': Contributor.objects.have_duplicate_email(),
            'nr_contributors_wo_profile': contributors_wo_profile.count(),
            'next_contributor_wo_profile': contributors_wo_profile.first(),
            'nr_refinv_wo_profile': refinv_wo_profile.count(),
            'next_refinv_wo_profile': refinv_wo_profile.first(),
            'nr_reginv_wo_profile': reginv_wo_profile.count(),
            'next_reginv_wo_profile': reginv_wo_profile.first(),
            'alternative_email_form': AlternativeEmailForm(),
        })
        return context


@permission_required('scipost.can_create_profiles')
def add_alternative_email(request, profile_id):
    """
    Add an alternative email address to a Profile.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    form = AlternativeEmailForm(request.POST or None, profile=profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Alternative email successfully added.')
    else:
        for field, err in form.errors.items():
            messages.warning(request, err[0])
    return redirect(reverse('profiles:profiles'))
