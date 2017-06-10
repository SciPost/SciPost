from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView, DeleteView

from guardian.decorators import permission_required

from .constants import PRODUCTION_STREAM_COMPLETED
from .models import ProductionStream, ProductionEvent
from .forms import ProductionEventForm


######################
# Production process #
######################

@permission_required('scipost.can_view_production', return_403=True)
def production(request):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    streams = ProductionStream.objects.ongoing().order_by('opened')
    prodevent_form = ProductionEventForm()
    context = {
        'streams': streams,
        'prodevent_form': prodevent_form,
    }
    return render(request, 'production/production.html', context)


@permission_required('scipost.can_view_production', return_403=True)
def completed(request):
    """
    Overview page for closed production streams.
    """
    streams = ProductionStream.objects.completed().order_by('-opened')
    context = {'streams': streams}
    return render(request, 'production/completed.html', context)


@permission_required('scipost.can_view_production', return_403=True)
def add_event(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    prodevent_form = ProductionEventForm(request.POST or None)
    if prodevent_form.is_valid():
        prodevent = prodevent_form.save(commit=False)
        prodevent.stream = stream
        prodevent.noted_by = request.user.contributor
        prodevent.save()
    else:
        messages.warning(request, 'The form was invalidly filled.')
    return redirect(reverse('production:production'))


@method_decorator(permission_required('scipost.can_view_production', raise_exception=True),
                  name='dispatch')
class UpdateEventView(UpdateView):
    model = ProductionEvent
    form_class = ProductionEventForm
    slug_field = 'id'
    slug_url_kwarg = 'event_id'

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.contributor)

    def form_valid(self, form):
        messages.success(self.request, 'Event updated succesfully')
        return super().form_valid(form)


@method_decorator(permission_required('scipost.can_view_production', raise_exception=True),
                  name='dispatch')
class DeleteEventView(DeleteView):
    model = ProductionEvent
    slug_field = 'id'
    slug_url_kwarg = 'event_id'

    def get_queryset(self):
        return self.model.objects.get_my_events(self.request.user.contributor)

    def form_valid(self, form):
        messages.success(self.request, 'Event deleted succesfully')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


@permission_required('scipost.can_publish_accepted_submission', return_403=True)
def mark_as_completed(request, stream_id):
    stream = get_object_or_404(ProductionStream.objects.ongoing(), pk=stream_id)
    stream.status = PRODUCTION_STREAM_COMPLETED
    stream.closed = timezone.now()
    stream.save()
    return redirect(reverse('production:production'))


def upload_proofs(request):
    """
    TODO
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    return render(request, 'production/upload_proofs.html')
