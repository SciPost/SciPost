__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from submissions.models import Submission

from .constants import (
    POTENTIAL_FELLOWSHIP_STATUSES, POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,
    POTENTIAL_FELLOWSHIP_INVITED, potential_fellowship_statuses_dict,
    POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON, POTENTIAL_FELLOWSHIP_EVENT_EMAILED)
from .forms import FellowshipForm, FellowshipTerminateForm, FellowshipRemoveSubmissionForm,\
    FellowshipAddSubmissionForm, AddFellowshipForm, SubmissionAddFellowshipForm,\
    FellowshipRemoveProceedingsForm, FellowshipAddProceedingsForm, SubmissionAddVotingFellowForm,\
    FellowVotingRemoveSubmissionForm,\
    PotentialFellowshipForm, PotentialFellowshipStatusForm, PotentialFellowshipEventForm
from .models import Fellowship, PotentialFellowship, PotentialFellowshipEvent

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin, PaginationMixin, RequestViewMixin

from mails.views import MailDetailView


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowships(request):
    """List all fellowships to be able to edit them, or create new ones."""
    fellowships = Fellowship.objects.active()

    context = {
        'fellowships': fellowships
    }
    return render(request, 'colleges/fellowships.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_detail(request, id):
    """View details of a specific fellowship."""
    fellowship = get_object_or_404(Fellowship, id=id)

    context = {
        'fellowship': fellowship
    }
    return render(request, 'colleges/fellowship_details.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_add(request):
    """
    Create a new Fellowship.
    """
    form = AddFellowshipForm(request.POST or None, initial=request.GET or None)

    if form.is_valid():
        fellowship = form.save()
        messages.success(request, 'Fellowship added.')
        return redirect(fellowship.get_absolute_url())

    context = {
        'form': form
    }
    return render(request, 'colleges/fellowship_add.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_edit(request, id):
    """
    Edit basic information about fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        messages.success(request, 'Fellowship updated.')
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form
    }
    return render(request, 'colleges/fellowship_edit.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_terminate(request, id):
    """
    Terminate Fellowship by setting the until_date to today's date.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipTerminateForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        messages.success(request, 'Fellowship terminated.')
    else:
        messages.warning(request, 'Fellowship has not been terminated, please try again.')
    return redirect(fellowship.get_absolute_url())


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def submission_pool(request, identifier_w_vn_nr):
    """
    List all Fellowships related to Submission.
    """
    submission = get_object_or_404(Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr)

    context = {
        'submission': submission
    }
    return render(request, 'colleges/submission_pool.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def submission_voting_fellows(request, identifier_w_vn_nr):
    """
    List all Fellowships selected for voting on the EIC related to Submission.
    """
    submission = get_object_or_404(Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr)

    context = {
        'submission': submission
    }
    return render(request, 'colleges/submission_voting_fellows.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def submission_add_fellowship_voting(request, identifier_w_vn_nr):
    """Add Fellowship to the Fellows voting on the EICRecommendation of a Submission."""
    submission = get_object_or_404(Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr)
    form = SubmissionAddVotingFellowForm(request.POST or None, instance=submission)

    if form.is_valid():
        form.save()
        messages.success(request, 'Fellowship {fellowship} ({id}) added to voting Fellows.'.format(
            fellowship=form.cleaned_data['fellowship'].contributor,
            id=form.cleaned_data['fellowship'].id))
        return redirect(reverse('colleges:submission_voting_fellows',
                                args=(submission.preprint.identifier_w_vn_nr,)))

    context = {
        'submission': submission,
        'form': form,
    }
    return render(request, 'colleges/submission_add_for_voting.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_remove_submission_voting(request, id, identifier_w_vn_nr):
    """Remove Fellow from the EICRecommendation voting group for the Submission."""
    fellowship = get_object_or_404(Fellowship, id=id)
    submission = get_object_or_404(
        fellowship.voting_pool.all(), preprint__identifier_w_vn_nr=identifier_w_vn_nr)
    form = FellowVotingRemoveSubmissionForm(request.POST or None,
                                            submission=submission, instance=fellowship)

    if form.is_valid() and request.POST:
        form.save()
        messages.success(request, 'Submission {submission_id} removed from Fellowship.'.format(
            submission_id=identifier_w_vn_nr))
        return redirect(reverse('colleges:submission_voting_fellows',
                                args=(submission.preprint.identifier_w_vn_nr,)))

    context = {
        'fellowship': fellowship,
        'form': form,
        'submission': submission
    }
    return render(request, 'colleges/fellowship_submission_remove_voting.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def submission_add_fellowship(request, identifier_w_vn_nr):
    """Add Fellowship to the pool of a Submission."""
    submission = get_object_or_404(Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr)
    form = SubmissionAddFellowshipForm(request.POST or None, instance=submission)

    if form.is_valid():
        form.save()
        messages.success(request, 'Fellowship {fellowship} ({id}) added to Submission.'.format(
            fellowship=form.cleaned_data['fellowship'].contributor,
            id=form.cleaned_data['fellowship'].id))
        return redirect(reverse('colleges:submission',
                                args=(submission.preprint.identifier_w_vn_nr,)))

    context = {
        'submission': submission,
        'form': form,
    }
    return render(request, 'colleges/submission_add.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_remove_submission(request, id, identifier_w_vn_nr):
    """Remove Submission from the pool of a Fellowship."""
    fellowship = get_object_or_404(Fellowship, id=id)
    submission = get_object_or_404(
        fellowship.pool.all(), preprint__identifier_w_vn_nr=identifier_w_vn_nr)
    form = FellowshipRemoveSubmissionForm(request.POST or None,
                                          submission=submission, instance=fellowship)

    if form.is_valid() and request.POST:
        form.save()
        messages.success(request, 'Submission {submission_id} removed from Fellowship.'.format(
            submission_id=identifier_w_vn_nr))
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form,
        'submission': submission
    }
    return render(request, 'colleges/fellowship_submission_remove.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_add_submission(request, id):
    """Add Submission to the pool of a Fellowship."""
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipAddSubmissionForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        messages.success(request, 'Submission {submission_id} added to Fellowship.'.format(
            submission_id=form.cleaned_data['submission'].preprint.identifier_w_vn_nr))
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form,
    }
    return render(request, 'colleges/fellowship_submission_add.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_remove_proceedings(request, id, proceedings_id):
    """
    Remove Proceedings from the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    proceedings = get_object_or_404(fellowship.proceedings.all(), id=proceedings_id)
    form = FellowshipRemoveProceedingsForm(request.POST or None,
                                           proceedings=proceedings, instance=fellowship)

    if form.is_valid() and request.POST:
        form.save()
        messages.success(request, 'Proceedings %s removed from Fellowship.' % str(proceedings))
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form,
        'proceedings': proceedings
    }
    return render(request, 'colleges/fellowship_proceedings_remove.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_add_proceedings(request, id):
    """
    Add Proceedings to the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipAddProceedingsForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        proceedings = form.cleaned_data.get('proceedings', '')
        messages.success(request, 'Proceedings %s added to Fellowship.' % str(proceedings))
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form,
    }
    return render(request, 'colleges/fellowship_proceedings_add.html', context)



# Potential Fellowships

class PotentialFellowshipCreateView(PermissionsMixin, RequestViewMixin, CreateView):
    """
    Formview to create a new Potential Fellowship.
    """
    permission_required = 'scipost.can_add_potentialfellowship'
    form_class = PotentialFellowshipForm
    template_name = 'colleges/potentialfellowship_form.html'
    success_url = reverse_lazy('colleges:potential_fellowships')


class PotentialFellowshipUpdateView(PermissionsMixin, RequestViewMixin, UpdateView):
    """
    Formview to update a Potential Fellowship.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = PotentialFellowship
    form_class = PotentialFellowshipForm
    template_name = 'colleges/potentialfellowship_form.html'
    success_url = reverse_lazy('colleges:potential_fellowships')


class PotentialFellowshipUpdateStatusView(PermissionsMixin, UpdateView):
    """
    Formview to update the status of a Potential Fellowship.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = PotentialFellowship
    fields = ['status']
    success_url = reverse_lazy('colleges:potential_fellowships')

    def form_valid(self, form):
        event = PotentialFellowshipEvent(
            potfel=self.object,
            event=POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,
            comments=('Status updated to %s'
                      % potential_fellowship_statuses_dict[form.cleaned_data['status']]),
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor)
        event.save()
        return super().form_valid(form)


class PotentialFellowshipDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Potential Fellowship.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = PotentialFellowship
    success_url = reverse_lazy('colleges:potential_fellowships')


class PotentialFellowshipListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List the PotentialFellowship object instances.
    """
    permission_required = 'scipost.can_view_potentialfellowship_list'
    model = PotentialFellowship
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of PotentialFellowships using optional GET data.
        """
        queryset = PotentialFellowship.objects.all()
        if self.kwargs.get('discipline', None):
            queryset = queryset.filter(profile__discipline=self.kwargs['discipline'].lower())
            if self.kwargs.get('expertise', None):
                queryset = queryset.filter(profile__expertises__contains=[self.kwargs['expertise']])
        if self.request.GET.get('status', None):
            queryset = queryset.filter(status=self.request.GET.get('status'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['potfels_to_vote_on'] = PotentialFellowship.objects.to_vote_on(
            self.request.user.contributor).annotate(
                nr_A=Count('in_agreement'), nr_N=Count('in_abstain'), nr_D=Count('in_disagreement'))
        context['potfels_voted_on'] = PotentialFellowship.objects.voted_on(
            self.request.user.contributor).annotate(
                nr_A=Count('in_agreement'), nr_N=Count('in_abstain'), nr_D=Count('in_disagreement'))
        context['subject_areas'] = SCIPOST_SUBJECT_AREAS
        context['statuses'] = POTENTIAL_FELLOWSHIP_STATUSES
        return context


class PotentialFellowshipDetailView(PermissionsMixin, DetailView):
    permission_required = 'scipost.can_view_potentialfellowship_list'
    model = PotentialFellowship

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pfstatus_form'] = PotentialFellowshipStatusForm()
        context['pfevent_form'] = PotentialFellowshipEventForm()
        return context


@login_required
@permission_required('scipost.can_vote_on_potentialfellowship', raise_exception=True)
def vote_on_potential_fellowship(request, potfel_id, vote):
    potfel = get_object_or_404(PotentialFellowship, pk=potfel_id)
    potfel.in_agreement.remove(request.user.contributor)
    potfel.in_abstain.remove(request.user.contributor)
    potfel.in_disagreement.remove(request.user.contributor)
    if vote == 'A':
        potfel.in_agreement.add(request.user.contributor)
        comments = 'Voted Agree'
    elif vote == 'N':
        potfel.in_abstain.add(request.user.contributor)
        comments = 'Voted Abstain'
    elif vote == 'D':
        potfel.in_disagreement.add(request.user.contributor)
        comments = 'Voted Disagree'
    else:
        raise Http404
    newevent = PotentialFellowshipEvent(
        potfel=potfel, event=POTENTIAL_FELLOWSHIP_EVENT_VOTED_ON,
        comments=comments, noted_by=request.user.contributor)
    newevent.save()
    return redirect(reverse('colleges:potential_fellowships'))


class PotentialFellowshipInitialEmailView(PermissionsMixin, MailDetailView):
    """Send a templated email to a Potential Fellow."""

    permission_required = 'scipost.can_manage_college_composition'
    queryset = PotentialFellowship.objects.all()
    mail_code = 'potentialfellowships/invite_potential_fellow_initial'
    success_url = reverse_lazy('colleges:potential_fellowships')

    def form_valid(self, form):
        """Create an event associated to this outgoing email."""
        event = PotentialFellowshipEvent(
            potfel=self.object,
            event=POTENTIAL_FELLOWSHIP_EVENT_EMAILED,
            comments='Emailed initial template to potential Fellow',
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor)
        event.save()
        self.object.status = POTENTIAL_FELLOWSHIP_INVITED
        self.object.save()
        return super().form_valid(form)


class PotentialFellowshipEventCreateView(PermissionsMixin, CreateView):
    """
    Add an event for a Potential Fellowship.
    """
    permission_required = 'scipost.can_manage_college_composition'
    form_class = PotentialFellowshipEventForm
    success_url = reverse_lazy('colleges:potential_fellowships')

    def form_valid(self, form):
        form.instance.potfel = get_object_or_404(PotentialFellowship, id=self.kwargs['pk'])
        form.instance.noted_on = timezone.now()
        form.instance.noted_by = self.request.user.contributor
        messages.success(self.request, 'Event added successfully')
        return super().form_valid(form)
