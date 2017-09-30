import datetime
import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView, DeleteView

from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, remove_perm

from . import constants
from .models import ProductionUser, ProductionStream, ProductionEvent, Proof
from .forms import ProductionEventForm, AssignOfficerForm, UserToOfficerForm,\
                   AssignSupervisorForm, StreamStatusForm, ProofUploadForm
from .permissions import is_production_user
from .signals import notify_stream_status_change,  notify_new_stream_assignment
from .utils import proof_slug_to_id


######################
# Production process #
######################

@is_production_user()
@permission_required('scipost.can_view_production', raise_exception=True)
def production(request):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    streams = ProductionStream.objects.ongoing()
    if not request.user.has_perm('scipost.can_view_all_production_streams'):
        # Restrict stream queryset if user is not supervisor
        streams = streams.filter_for_user(request.user.production_user)
    streams = streams.order_by('opened')

    ownevents = ProductionEvent.objects.filter(
        noted_by=request.user.production_user,
        duration__gte=datetime.timedelta(minutes=1)).order_by('-noted_on')
    context = {
        'streams': streams,
        'ownevents': ownevents,
    }
    if request.user.has_perm('scipost.can_view_timesheets'):
        context['production_team'] = ProductionUser.objects.all()

    if request.user.has_perm('scipost.can_promote_to_production_team'):
        context['production_officers'] = ProductionUser.objects.all()
        context['new_officer_form'] = UserToOfficerForm()
    return render(request, 'production/production.html', context)


@is_production_user()
@permission_required('scipost.can_view_production', raise_exception=True)
def completed(request):
    """
    Overview page for closed production streams.
    """
    streams = ProductionStream.objects.completed()
    if not request.user.has_perm('scipost.can_view_all_production_streams'):
        streams = streams.filter_for_user(request.user.production_user)
    streams = streams.order_by('-opened')

    context = {'streams': streams}
    return render(request, 'production/completed.html', context)


@is_production_user()
@permission_required('scipost.can_view_production', raise_exception=True)
def stream(request, stream_id):
    """
    Overview page for specific stream.
    """
    streams = ProductionStream.objects.ongoing()
    if not request.user.has_perm('scipost.can_view_all_production_streams'):
        # Restrict stream queryset if user is not supervisor
        streams = streams.filter_for_user(request.user.production_user)
    stream = get_object_or_404(streams, id=stream_id)
    prodevent_form = ProductionEventForm()
    assign_officer_form = AssignOfficerForm()
    assign_supervisor_form = AssignSupervisorForm()
    status_form = StreamStatusForm(instance=stream, production_user=request.user.production_user)

    context = {
        'stream': stream,
        'prodevent_form': prodevent_form,
        'assign_officer_form': assign_officer_form,
        'assign_supervisor_form': assign_supervisor_form,
        'status_form': status_form,
    }

    if request.GET.get('json'):
        return render(request, 'production/partials/production_stream_card.html', context)
    else:
        return render(request, 'production/stream.html', context)


@is_production_user()
@permission_required('scipost.can_promote_user_to_production_officer')
def user_to_officer(request):
    form = UserToOfficerForm(request.POST or None)
    if form.is_valid():
        officer = form.save()

        # Add permission group
        group = Group.objects.get(name='Production Officers')
        officer.user.groups.add(group)
        messages.success(request, '{user} promoted to Production Officer'.format(user=officer))
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_take_decisions_related_to_proofs', raise_exception=True)
def update_status(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_perform_supervisory_actions', stream):
        return redirect(reverse('production:production'))

    p = request.user.production_user
    form = StreamStatusForm(request.POST or None, instance=stream,
                            production_user=p)

    if form.is_valid():
        stream = form.save()
        messages.warning(request, 'Production Stream succesfully changed status.')
    else:
        messages.warning(request, 'The status change was invalid.')
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required('scipost.can_view_production', raise_exception=True)
def add_event(request, stream_id):
    qs = ProductionStream.objects.ongoing()
    if not request.user.has_perm('scipost.can_assign_production_officer'):
        qs = qs.filter_for_user(request.user.production_user)

    stream = get_object_or_404(qs, pk=stream_id)
    prodevent_form = ProductionEventForm(request.POST or None)
    if prodevent_form.is_valid():
        prodevent = prodevent_form.save(commit=False)
        prodevent.stream = stream
        if prodevent.duration:
            prodevent.event = constants.EVENT_HOUR_REGISTRATION
        prodevent.noted_by = request.user.production_user
        prodevent.save()
    else:
        messages.warning(request, 'The form was invalidly filled.')
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_officer', raise_exception=True)
def add_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_perform_supervisory_actions', stream):
        return redirect(reverse('production:production'))

    form = AssignOfficerForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        officer = form.cleaned_data.get('officer')
        assign_perm('can_work_for_stream', officer.user, stream)
        messages.success(request, 'Officer {officer} has been assigned.'.format(officer=officer))
        notify_new_stream_assignment(request.user, stream, officer.user)
        event = ProductionEvent(
            stream=stream,
            event='assignment',
            comments=' tasked Production Officer with proofs production:',
            noted_to=officer,
            noted_by=request.user.production_user)
        event.save()
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_officer', raise_exception=True)
def remove_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_perform_supervisory_actions', stream):
        return redirect(reverse('production:production'))

    if getattr(stream.officer, 'id', 0) == int(officer_id):
        officer = stream.officer
        stream.officer = None
        stream.save()
        remove_perm('can_work_for_stream', officer.user, stream)
        messages.success(request, 'Officer {officer} has been removed.'.format(officer=officer))

    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_supervisor', raise_exception=True)
@transaction.atomic
def add_supervisor(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    form = AssignSupervisorForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        supervisor = form.cleaned_data.get('supervisor')
        messages.success(request, 'Supervisor {supervisor} has been assigned.'.format(
            supervisor=supervisor))
        notify_new_stream_assignment(request.user, stream, supervisor.user)
        event = ProductionEvent(
            stream=stream,
            event='assignment',
            comments=' assigned Production Supervisor:',
            noted_to=supervisor,
            noted_by=request.user.production_user)
        event.save()

        assign_perm('can_work_for_stream', supervisor.user, stream)
        assign_perm('can_perform_supervisory_actions', supervisor.user, stream)
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_supervisor', raise_exception=True)
def remove_supervisor(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    if getattr(stream.supervisor, 'id', 0) == int(officer_id):
        supervisor = stream.supervisor
        stream.supervisor = None
        stream.save()
        remove_perm('can_work_for_stream', supervisor.user, stream)
        remove_perm('can_perform_supervisory_actions', supervisor.user, stream)
        messages.success(request, 'Supervisor {supervisor} has been removed.'.format(
            supervisor=supervisor))

    return redirect(reverse('production:production'))


@method_decorator(is_production_user(), name='dispatch')
@method_decorator(permission_required('scipost.can_view_production', raise_exception=True),
                  name='dispatch')
class UpdateEventView(UpdateView):
    model = ProductionEvent
    form_class = ProductionEventForm
    slug_field = 'id'
    slug_url_kwarg = 'event_id'

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.production_user)

    def form_valid(self, form):
        messages.success(self.request, 'Event updated succesfully')
        return super().form_valid(form)


@method_decorator(is_production_user(), name='dispatch')
@method_decorator(permission_required('scipost.can_view_production', raise_exception=True),
                  name='dispatch')
class DeleteEventView(DeleteView):
    model = ProductionEvent
    slug_field = 'id'
    slug_url_kwarg = 'event_id'

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.production_user)

    def form_valid(self, form):
        messages.success(self.request, 'Event deleted succesfully')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


@is_production_user()
@permission_required('scipost.can_publish_accepted_submission', raise_exception=True)
def mark_as_completed(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    stream.status = constants.PRODUCTION_STREAM_COMPLETED
    stream.closed = timezone.now()
    stream.save()

    prodevent = ProductionEvent(
        stream=stream,
        event='status',
        comments=' marked the Production Stream as completed.',
        noted_by=request.user.production_user
    )
    prodevent.save()
    notify_stream_status_change(request.user, stream)
    messages.success(request, 'Stream marked as completed.')
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_upload_proofs', raise_exception=True)
def upload_proofs(request, stream_id):
    """
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_work_for_stream', stream):
        return redirect(reverse('production:production'))

    form = ProofUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        proof = form.save(commit=False)
        proof.stream = stream
        proof.uploaded_by = request.user.production_user
        proof.save()
        Proof.objects.filter(stream=stream).exclude(version=proof.version).update(
            status=constants.PROOF_RENEWED)
        messages.success(request, 'Proof uploaded.')

        # Update Stream status
        if stream.status == constants.PROOFS_TASKED:
            stream.status = constants.PROOFS_PRODUCED
            stream.save()
        elif stream.status == constants.PROOFS_RETURNED:
            stream.status = constants.PROOFS_CORRECTED
            stream.save()

        prodevent = ProductionEvent(
            stream=stream,
            event='status',
            comments='New Proofs uploaded, version {v}'.format(v=proof.version),
            noted_by=request.user.production_user
        )
        prodevent.save()
        return redirect(stream.get_absolute_url())

    context = {
        'stream': stream,
        'form': form
    }
    return render(request, 'production/upload_proofs.html', context)


@is_production_user()
@permission_required('scipost.can_view_production', raise_exception=True)
def proof(request, stream_id, version):
    """
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    stream = get_object_or_404(ProductionStream.objects.all(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_work_for_stream', stream):
        return redirect(reverse('production:production'))

    try:
        proof = stream.proofs.get(version=version)
    except Proof.DoesNotExist:
        raise Http404

    context = {
        'stream': stream,
        'proof': proof
    }
    return render(request, 'production/proofs.html', context)


def proof_pdf(request, slug):
    """ Open Proof pdf. """
    if not request.user.is_authenticated:
        # Don't use the decorator but this strategy,
        # because now it will return 404 instead of a redirect to the login page.
        raise Http404

    proof = Proof.objects.get(id=proof_slug_to_id(slug))
    stream = proof.stream

    # Check if user has access!
    checker = ObjectPermissionChecker(request.user)
    access = checker.has_perm('can_work_for_stream', stream) and request.user.has_perm('scipost.can_view_production')
    if not access:
        access = request.user in proof.stream.submission.authors.all()
    if not access:
        raise Http404

    # Passed the test! The user may see the file!
    content_type, encoding = mimetypes.guess_type(proof.attachment.path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(proof.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    return response


@is_production_user()
@permission_required('scipost.can_run_proofs_by_authors', raise_exception=True)
def toggle_accessibility(request, stream_id, version):
    """
    Open/close accessibility of proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.all(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_work_for_stream', stream):
        return redirect(reverse('production:production'))

    try:
        proof = stream.proofs.exclude(status=constants.PROOF_UPLOADED).get(version=version)
    except Proof.DoesNotExist:
        raise Http404

    proof.accessible_for_authors = not proof.accessible_for_authors
    proof.save()
    messages.success(request, 'Proofs accessibility updated.')
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required('scipost.can_run_proofs_by_authors', raise_exception=True)
def decision(request, stream_id, version, decision):
    """
    Send/open proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_work_for_stream', stream):
        return redirect(reverse('production:production'))

    try:
        proof = stream.proofs.get(version=version, status=constants.PROOF_UPLOADED)
    except Proof.DoesNotExist:
        raise Http404

    if decision == 'accept':
        proof.status = constants.PROOF_ACCEPTED_SUP
        stream.status = constants.PROOFS_CHECKED
        decision = 'accepted'
    else:
        proof.status = constants.PROOF_DECLINED_SUP
        stream.status = constants.PROOFS_TASKED
        decision = 'declined'
    stream.save()
    proof.save()

    prodevent = ProductionEvent(
        stream=stream,
        event='status',
        comments='Proofs version {version} are {decision}.'.format(version=proof.version,
                                                                   decision=decision),
        noted_by=request.user.production_user
    )
    prodevent.save()
    messages.success(request, 'Proofs have been {decision}.'.format(decision=decision))
    return redirect(stream.get_absolute_url())


@is_production_user()
@permission_required('scipost.can_run_proofs_by_authors', raise_exception=True)
def send_proofs(request, stream_id, version):
    """
    Send/open proofs to the authors.
    """
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    checker = ObjectPermissionChecker(request.user)
    if not checker.has_perm('can_work_for_stream', stream):
        return redirect(reverse('production:production'))

    try:
        proof = stream.proofs.get(version=version, status=constants.PROOF_UPLOADED)
    except Proof.DoesNotExist:
        raise Http404

    proof.status = constants.PROOF_SENT
    proof.accessible_for_authors = True
    proof.save()

    if stream.status not in [constants.PROOFS_PUBLISHED, constants.PROOFS_CITED]:
        stream.status = constants.PROOFS_SENT
        stream.save()

    messages.success(request, 'Proofs have been sent.')
    return redirect(stream.get_absolute_url())
