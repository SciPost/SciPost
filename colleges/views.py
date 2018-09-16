__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from submissions.models import Submission

from .constants import POTENTIAL_FELLOWSHIP_INVITED, potential_fellowship_statuses_dict,\
    POTENTIAL_FELLOWSHIP_EVENT_EMAILED, POTENTIAL_FELLOWSHIP_EVENT_STATUSUPDATED,\
    POTENTIAL_FELLOWSHIP_EVENT_COMMENT
# NEXT IMPORTS TO BE DEPRECATED
from .constants import PROSPECTIVE_FELLOW_INVITED,\
    prospective_Fellow_statuses_dict,\
    PROSPECTIVE_FELLOW_EVENT_EMAILED, PROSPECTIVE_FELLOW_EVENT_STATUSUPDATED,\
    PROSPECTIVE_FELLOW_EVENT_COMMENT
from .forms import FellowshipForm, FellowshipTerminateForm, FellowshipRemoveSubmissionForm,\
    FellowshipAddSubmissionForm, AddFellowshipForm, SubmissionAddFellowshipForm,\
    FellowshipRemoveProceedingsForm, FellowshipAddProceedingsForm, SubmissionAddVotingFellowForm,\
    FellowVotingRemoveSubmissionForm,\
    PotentialFellowshipForm, PotentialFellowshipStatusForm, PotentialFellowshipEventForm,\
    ProspectiveFellowForm, ProspectiveFellowStatusForm, ProspectiveFellowEventForm
from .models import Fellowship, PotentialFellowship, PotentialFellowshipEvent,\
    ProspectiveFellow, ProspectiveFellowEvent

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.mixins import PermissionsMixin

from mails.forms import EmailTemplateForm
from mails.views import MailView


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

class PotentialFellowshipCreateView(PermissionsMixin, CreateView):
    """
    Formview to create a new Potential Fellowship.
    """
    permission_required = 'scipost.can_manage_college_composition'
    form_class = PotentialFellowshipForm
    template_name = 'colleges/potentialfellowship_form.html'
    success_url = reverse_lazy('colleges:potential_fellowships')


class PotentialFellowshipUpdateView(PermissionsMixin, UpdateView):
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


class PotentialFellowshipListView(PermissionsMixin, ListView):
    """
    List the PotentialFellowship object instances.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = PotentialFellowship
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of PotentialFellowships using optional GET data.
        """
        queryset = PotentialFellowship.objects.all()
        if 'discipline' in self.request.GET:
            queryset = queryset.filter(discipline=self.request.GET['discipline'].lower())
            if 'expertise' in self.request.GET:
                queryset = queryset.filter(expertises__contains=[self.request.GET['expertise']])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_areas'] = SCIPOST_SUBJECT_AREAS
        context['pfstatus_form'] = PotentialFellowshipStatusForm()
        context['pfevent_form'] = PotentialFellowshipEventForm()
        return context


class PotentialFellowshipInitialEmailView(PermissionsMixin, MailView):
    """Send a templated email to a Potential Fellow."""

    permission_required = 'scipost.can_manage_college_composition'
    queryset = PotentialFellowship.objects.all()
    mail_code = 'potentialfellows/invite_potential_fellow_initial'
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


# TO BE DEPRECATED:
class ProspectiveFellowCreateView(PermissionsMixin, CreateView):
    """
    Formview to create a new Prospective Fellow.
    """
    permission_required = 'scipost.can_manage_college_composition'
    form_class = ProspectiveFellowForm
    template_name = 'colleges/prospectivefellow_form.html'
    success_url = reverse_lazy('colleges:prospective_Fellows')


class ProspectiveFellowUpdateView(PermissionsMixin, UpdateView):
    """
    Formview to update a Prospective Fellow.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = ProspectiveFellow
    form_class = ProspectiveFellowForm
    template_name = 'colleges/prospectivefellow_form.html'
    success_url = reverse_lazy('colleges:prospective_Fellows')


class ProspectiveFellowUpdateStatusView(PermissionsMixin, UpdateView):
    """
    Formview to update the status of a Prospective Fellow.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = ProspectiveFellow
    fields = ['status']
    success_url = reverse_lazy('colleges:prospective_Fellows')

    def form_valid(self, form):
        event = ProspectiveFellowEvent(
            prosfellow=self.object,
            event=PROSPECTIVE_FELLOW_EVENT_STATUSUPDATED,
            comments=('Status updated to %s'
                      % prospective_Fellow_statuses_dict[form.cleaned_data['status']]),
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor)
        event.save()
        return super().form_valid(form)


class ProspectiveFellowDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Prospective Fellow.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = ProspectiveFellow
    success_url = reverse_lazy('colleges:prospective_Fellows')


class ProspectiveFellowListView(PermissionsMixin, ListView):
    """
    List the ProspectiveFellow object instances.
    """
    permission_required = 'scipost.can_manage_college_composition'
    model = ProspectiveFellow
    paginate_by = 50

    def get_queryset(self):
        """
        Return a queryset of ProspectiveFellows using optional GET data.
        """
        queryset = ProspectiveFellow.objects.all()
        if 'discipline' in self.request.GET:
            queryset = queryset.filter(discipline=self.request.GET['discipline'].lower())
            if 'expertise' in self.request.GET:
                queryset = queryset.filter(expertises__contains=[self.request.GET['expertise']])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_areas'] = SCIPOST_SUBJECT_AREAS
        context['pfstatus_form'] = ProspectiveFellowStatusForm()
        context['pfevent_form'] = ProspectiveFellowEventForm()
        return context


class ProspectiveFellowInitialEmailView(PermissionsMixin, MailView):
    """Send a templated email to a Prospective Fellow."""

    permission_required = 'scipost.can_manage_college_composition'
    queryset = ProspectiveFellow.objects.all()
    mail_code = 'prospectivefellows/invite_prospective_fellow_initial'
    success_url = reverse_lazy('colleges:prospective_Fellows')

    def form_valid(self, form):
        """Create an event associated to this outgoing email."""
        event = ProspectiveFellowEvent(
            prosfellow=self.object,
            event=PROSPECTIVE_FELLOW_EVENT_EMAILED,
            comments='Emailed initial template',
            noted_on=timezone.now(),
            noted_by=self.request.user.contributor)
        event.save()
        self.object.status = PROSPECTIVE_FELLOW_INVITED
        self.object.save()
        return super().form_valid(form)


class ProspectiveFellowEventCreateView(PermissionsMixin, CreateView):
    """
    Add an event for a Prospective Fellow.
    """
    permission_required = 'scipost.can_manage_college_composition'
    form_class = ProspectiveFellowEventForm
    success_url = reverse_lazy('colleges:prospective_Fellows')

    def form_valid(self, form):
        form.instance.prosfellow = get_object_or_404(ProspectiveFellow, id=self.kwargs['pk'])
        form.instance.noted_on = timezone.now()
        form.instance.noted_by = self.request.user.contributor
        messages.success(self.request, 'Event added successfully')
        return super().form_valid(form)
