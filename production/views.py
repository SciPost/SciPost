from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from .models import ProductionStream, ProductionEvent
from .forms import ProductionEventForm

from submissions.models import Submission
from scipost.models import Contributor


######################
# Production process #
######################

@permission_required('scipost.can_view_production', return_403=True)
def production(request):
    """
    Overview page for the production process.
    All papers with accepted but not yet published status are included here.
    """
    accepted_submissions = Submission.objects.filter(
        status='accepted').order_by('latest_activity')
    streams = ProductionStream.objects.all().order_by('opened')
    prodevent_form = ProductionEventForm()
    context = {
        'accepted_submissions': accepted_submissions,
        'streams': streams,
        'prodevent_form': prodevent_form,
    }
    return render(request, 'production/production.html', context)

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




def upload_proofs(request):
    """
    TODO
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    return render(request, 'production/upload_proofs.html')
