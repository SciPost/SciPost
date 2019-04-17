__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin, PaginationMixin
from scipost.models import Contributor
from scipost.forms import SearchTextForm

from common.utils import Q_with_alternative_spellings
from invitations.models import RegistrationInvitation
from submissions.models import RefereeInvitation

from .models import Profile, ProfileEmail, Affiliation
from .forms import ProfileForm, ProfileMergeForm, ProfileEmailForm, AffiliationForm



class ProfileCreateView(PermissionsMixin, CreateView):
    """
    Formview to create a new Profile.
    """
    permission_required = 'scipost.can_create_profiles'
    form_class = ProfileForm
    template_name = 'profiles/profile_form.html'
    success_url = reverse_lazy('profiles:profiles')

    def get_context_data(self, *args, **kwargs):
        """
        When creating a Profile, if initial data obtained from another model
        (Contributor, RefereeInvitation or RegistrationInvitation)
        is provided, this fills the context with possible already-existing Profiles.
        """
        context = super().get_context_data(*args, **kwargs)
        from_type = self.kwargs.get('from_type', None)
        pk = self.kwargs.get('pk', None)
        context['from_type'] = from_type
        context['pk'] = pk
        if pk and from_type:
            matching_profiles = Profile.objects.all()
            if from_type == 'contributor':
                contributor = get_object_or_404(Contributor, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=contributor.user.last_name) |
                    Q(emails__email__in=contributor.user.email))
            elif from_type == 'refereeinvitation':
                print ('Here refinv')
                refinv = get_object_or_404(RefereeInvitation, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=refinv.last_name) |
                    Q(emails__email__in=refinv.email_address))
            elif from_type == 'registrationinvitation':
                reginv = get_object_or_404(RegistrationInvitation, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=reginv.last_name) |
                    Q(emails__email__in=reginv.email))
            context['matching_profiles'] = matching_profiles.distinct().order_by(
                'last_name', 'first_name')
        return context

    def get_initial(self):
        """
        Provide initial data based on kwargs.
        The data can come from a Contributor, Invitation, ...
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
            initial.update({
                'instance_from_type': from_type,
                'instance_pk': pk,
            })
        return initial

@permission_required('scipost.can_create_profiles')
def profile_match(request, profile_id, from_type, pk):
    """
    Links an existing Profile to one of existing
    Contributor, RefereeInvitation or RegistrationInvitation.

    Profile relates to Contributor as OneToOne.
    Matching is thus only allowed if there are no duplicate objects for these elements.

    For matching the Profile to a Contributor, the following preconditions are defined:
    - the Profile has no association to another Contributor
    - the Contributor has no association to another Profile
    If these are not met, no action is taken.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    nr_rows = 0
    if from_type == 'contributor':
        if hasattr(profile, 'contributor') and profile.contributor.id != pk:
            messages.error(request,
                           'Error: cannot math this Profile to this Contributor, '
                           'since this Profile already has a different Contributor.\n'
                           'Please merge the duplicate Contributors first.')
            return redirect(reverse('profiles:profiles'))
        contributor = get_object_or_404(Contributor, pk=pk)
        if contributor.profile and contributor.profile.id != profile.id:
            messages.error(request,
                           'Error: cannot match this Profile to this Contributor, '
                           'since this Contributor already has a different Profile.\n'
                           'Please merge the duplicate Profiles first.')
            return redirect(reverse('profiles:profiles'))
        # Preconditions are met, match:
        nr_rows = Contributor.objects.filter(pk=pk).update(profile=profile)
        # Give priority to the email coming from Contributor
        profile.emails.update(primary=False)
        email, __ = ProfileEmail.objects.get_or_create(
            profile=profile, email=contributor.user.email)
        profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
    elif from_type == 'refereeinvitation':
        nr_rows = RefereeInvitation.objects.filter(pk=pk).update(profile=profile)
    elif from_type == 'registrationinvitation':
        nr_rows = RegistrationInvitation.objects.filter(pk=pk).update(profile=profile)
    if nr_rows == 1:
        messages.success(request, 'Profile matched with %s' % from_type)
    else:
        messages.error(
            request,
            'Error: Profile matching with %s: updated %s rows instead of 1!'
            'Please contact techsupport' % (from_type, nr_rows))
    return redirect(reverse('profiles:profiles'))


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


class ProfileDetailView(PermissionsMixin, DetailView):
    permission_required = 'scipost.can_view_profiles'
    model = Profile

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['email_form'] = ProfileEmailForm()
        return context


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
            query = Q_with_alternative_spellings(
                last_name__istartswith=self.request.GET['text'])
            queryset = queryset.filter(query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contributors_w_duplicate_email = Contributor.objects.with_duplicate_email()
        contributors_w_duplicate_names = Contributor.objects.with_duplicate_names()
        contributors_wo_profile = Contributor.objects.nonduplicates().filter(profile__isnull=True)
        nr_potential_duplicate_profiles = Profile.objects.potential_duplicates().count()
        refinv_wo_profile = RefereeInvitation.objects.filter(profile__isnull=True)
        reginv_wo_profile = RegistrationInvitation.objects.filter(profile__isnull=True)

        context.update({
            'subject_areas': SCIPOST_SUBJECT_AREAS,
            'searchform': SearchTextForm(initial={'text': self.request.GET.get('text')}),
            'nr_contributors_w_duplicate_emails': contributors_w_duplicate_email.count(),
            'nr_contributors_w_duplicate_names': contributors_w_duplicate_names.count(),
            'nr_contributors_wo_profile': contributors_wo_profile.count(),
            'nr_potential_duplicate_profiles': nr_potential_duplicate_profiles,
            'next_contributor_wo_profile': contributors_wo_profile.first(),
            'nr_refinv_wo_profile': refinv_wo_profile.count(),
            'next_refinv_wo_profile': refinv_wo_profile.first(),
            'nr_reginv_wo_profile': reginv_wo_profile.count(),
            'next_reginv_wo_profile': reginv_wo_profile.first(),
            'email_form': ProfileEmailForm(),
        })
        return context


class ProfileDuplicateListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List Profiles with potential duplicates; allow to merge if necessary.
    """
    permission_required = 'scipost.can_create_profiles'
    model = Profile
    template_name = 'profiles/profile_duplicate_list.html'
    paginate_by = 16

    def get_queryset(self):
        return Profile.objects.potential_duplicates()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if len(context['object_list']) > 1:
            initial = {
                'to_merge': context['object_list'][0].id,
                'to_merge_into': context['object_list'][1].id
            }
            context['merge_form'] = ProfileMergeForm(initial=initial)
        return context


@transaction.atomic
@permission_required('scipost.can_create_profiles')
def profile_merge(request):
    """
    Merges one Profile into another.
    """
    merge_form = ProfileMergeForm(request.POST or None, initial=request.GET)
    context = {'merge_form': merge_form}

    if request.method == 'POST':
        if merge_form.is_valid():
            profile = merge_form.save()
            messages.success(request, 'Profiles merged')
            return redirect(profile.get_absolute_url())
        else:
            try:
                context.update({
                    'profile_to_merge': get_object_or_404(
                        Profile, pk=merge_form.cleaned_data['to_merge'].id),
                    'profile_to_merge_into': get_object_or_404(
                        Profile, pk=merge_form.cleaned_data['to_merge_into'].id)
                })
            except ValueError:
                raise Http404

    elif request.method == 'GET':
        try:
            context.update({
                'profile_to_merge': get_object_or_404(Profile,
                                                      pk=int(request.GET['to_merge'])),
                'profile_to_merge_into': get_object_or_404(Profile,
                                                           pk=int(request.GET['to_merge_into']))
            })
        except ValueError:
            raise Http404

    return render(request, 'profiles/profile_merge.html', context)


@permission_required('scipost.can_create_profiles')
def add_profile_email(request, profile_id):
    """
    Add an email address to a Profile.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    form = ProfileEmailForm(request.POST or None, profile=profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Email successfully added.')
    else:
        for field, err in form.errors.items():
            messages.warning(request, err[0])
    if request.POST.get('next', None):
        return HttpResponseRedirect(request.POST.get('next'))
    return redirect(profile.get_absolute_url())


@require_POST
@permission_required('scipost.can_create_profiles')
def email_make_primary(request, email_id):
    """
    Make this email the primary one for this Profile.
    """
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)
    ProfileEmail.objects.filter(profile=profile_email.profile).update(primary=False)
    profile_email.primary = True
    profile_email.save()
    return redirect(profile_email.profile.get_absolute_url())


@require_POST
@permission_required('scipost.can_create_profiles')
def toggle_email_status(request, email_id):
    """Toggle valid/deprecated status of ProfileEmail."""
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)
    ProfileEmail.objects.filter(id=email_id).update(still_valid=not profile_email.still_valid)
    messages.success(request, 'Email updated')
    return redirect(profile_email.profile.get_absolute_url())


@require_POST
@permission_required('scipost.can_create_profiles')
def delete_profile_email(request, email_id):
    """Delete ProfileEmail."""
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)
    profile_email.delete()
    messages.success(request, 'Email deleted')
    return redirect(profile_email.profile.get_absolute_url())


class AffiliationCreateView(UserPassesTestMixin, CreateView):
    model = Affiliation
    form_class = AffiliationForm
    template_name = 'profiles/affiliation_form.html'

    def test_func(self):
        """
        Allow creating an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return True
        return (self.request.user.is_authenticated and
                self.request.user.contributor.profile.id == int(self.kwargs.get('profile_id')))

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        profile = get_object_or_404(Profile, pk=self.kwargs.get('profile_id'))
        initial.update({
            'profile': profile
        })
        return initial

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return reverse_lazy('profiles:profile_detail',
                                kwargs={'pk': self.object.profile.id})
        return reverse_lazy('scipost:personal_page')


class AffiliationUpdateView(UserPassesTestMixin, UpdateView):
    model = Affiliation
    form_class = AffiliationForm
    template_name = 'profiles/affiliation_form.html'

    def test_func(self):
        """
        Allow updating an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return True
        return (self.request.user.is_authenticated and
                self.request.user.contributor.profile.id == int(self.kwargs.get('profile_id')))

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return reverse_lazy('profiles:profile_detail',
                                kwargs={'pk': self.object.profile.id})
        return reverse_lazy('scipost:personal_page')


class AffiliationDeleteView(UserPassesTestMixin, DeleteView):
    model = Affiliation

    def test_func(self):
        """
        Allow deleting an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return True
        return (self.request.user.is_authenticated and
                self.request.user.contributor.profile.id == int(self.kwargs.get('profile_id')))

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm('scipost.can_create_profiles'):
            return reverse_lazy('profiles:profile_detail',
                                kwargs={'pk': self.object.profile.id})
        return reverse_lazy('scipost:personal_page')
