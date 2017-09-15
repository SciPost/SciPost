import datetime

from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView, DeleteView

from guardian.decorators import permission_required

from .constants import PRODUCTION_STREAM_COMPLETED
from .models import ProductionUser, ProductionStream, ProductionEvent
from .forms import ProductionEventForm, AssignOfficerForm, UserToOfficerForm
from .permissions import is_production_user
from .signals import notify_stream_completed, notify_new_stream_assignment


######################
# Production process #
######################

@is_production_user()
@permission_required('scipost.can_view_production', return_403=True)
def production(request):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    streams = ProductionStream.objects.ongoing()
    if not request.user.has_perm('scipost.can_assign_production_officer'):
        # Restrict stream queryset if user is not supervisor
        streams = streams.filter_for_user(request.user.production_user)
    streams = streams.order_by('opened')

    prodevent_form = ProductionEventForm()
    assignment_form = AssignOfficerForm()
    ownevents = ProductionEvent.objects.filter(
        noted_by=request.user.production_user,
        duration__gte=datetime.timedelta(minutes=1)).order_by('-noted_on')
    context = {
        'streams': streams,
        'prodevent_form': prodevent_form,
        'assignment_form': assignment_form,
        'ownevents': ownevents,
    }
    if request.user.has_perm('scipost.can_view_timesheets'):
        context['production_team'] = ProductionUser.objects.all()

    if request.user.has_perm('scipost.can_promote_user_to_production_officer'):
        context['production_officers'] = ProductionUser.objects.all()
        context['new_officer_form'] = UserToOfficerForm()
    return render(request, 'production/production.html', context)


@is_production_user()
@permission_required('scipost.can_view_production', return_403=True)
def completed(request):
    """
    Overview page for closed production streams.
    """
    streams = ProductionStream.objects.completed().order_by('-opened')
    context = {'streams': streams}
    return render(request, 'production/completed.html', context)


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
@permission_required('scipost.can_view_production', return_403=True)
def add_event(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    prodevent_form = ProductionEventForm(request.POST or None)
    if prodevent_form.is_valid():
        prodevent = prodevent_form.save(commit=False)
        prodevent.stream = stream
        prodevent.noted_by = request.user.production_user
        prodevent.save()
    else:
        messages.warning(request, 'The form was invalidly filled.')
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_officer', return_403=True)
def add_officer(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    form = AssignOfficerForm(request.POST or None, instance=stream)
    if form.is_valid():
        form.save()
        officer = form.cleaned_data.get('officer')
        messages.success(request, 'Officer {officer} has been assigned.'.format(officer=officer))
        notify_new_stream_assignment(request.user, stream, officer.user)
    else:
        for key, error in form.errors.items():
            messages.warning(request, error[0])
    return redirect(reverse('production:production'))


@is_production_user()
@permission_required('scipost.can_assign_production_officer', return_403=True)
def remove_officer(request, stream_id, officer_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    try:
        officer = stream.officers.get(pk=officer_id)
    except ProductionUser.DoesNotExist:
        return redirect(reverse('production:production'))

    stream.officers.remove(officer)
    messages.success(request, 'Officer {officer} has been removed.'.format(officer=officer))
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
@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_as_completed(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    stream.status = PRODUCTION_STREAM_COMPLETED
    stream.closed = timezone.now()
    stream.save()

    notify_stream_completed(request.user, stream)
    return redirect(reverse('production:production'))


def upload_proofs(request):
    """
    TODO
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    return render(request, 'production/upload_proofs.html')
