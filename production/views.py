from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from .models import ProductionStream, ProductionEvent
from .forms import ProductionEventForm

from submissions.models import Submission


######################
# Production process #
######################

@permission_required('scipost.can_view_production', return_403=True)
def production(request):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    streams = ProductionStream.objects.filter(status='ongoing').order_by('opened')
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
    streams = ProductionStream.objects.filter(status='completed').order_by('-opened')
    context = {'streams': streams,}
    return render(request, 'production/completed.html', context)


@permission_required('scipost.can_view_production', return_403=True)
@transaction.atomic
def add_event(request, stream_id):
    stream = get_object_or_404(ProductionStream, pk=stream_id)
    if request.method == 'POST':
        prodevent_form = ProductionEventForm(request.POST)
        if prodevent_form.is_valid():
            prodevent = ProductionEvent(
                stream=stream,
                event=prodevent_form.cleaned_data['event'],
                comments=prodevent_form.cleaned_data['comments'],
                noted_on=timezone.now(),
                noted_by=request.user.contributor,
                duration=prodevent_form.cleaned_data['duration'],)
            prodevent.save()
            return redirect(reverse('production:production'))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@permission_required('scipost.can_view_production', return_403=True)
@transaction.atomic
def mark_as_completed(request, stream_id):
    stream = get_object_or_404(ProductionStream, pk=stream_id)
    stream.status = 'completed'
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
