import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from submissions.models import Submission

from guardian.decorators import permission_required
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm

############
# Journals 
############


def journals(request):
    return render(request, 'journals/journals.html')


def scipost_physics(request):
    #return render(request, 'journals/scipost_physics.html')
    return redirect(reverse('journals:scipost_physics_accepted'))


def scipost_physics_info_for_authors(request):
    return render(request, 'journals/scipost_physics_info_for_authors.html')

def scipost_physics_about(request):
    return render(request, 'journals/scipost_physics_about.html')


def scipost_physics_accepted(request):
    """
    Display page for submissions to SciPost Physics which
    have been accepted but are not yet published.
    """
    accepted_SP_submissions = Submission.objects.filter(
        submitted_to_journal='SciPost Physics', status='accepted'
    ).order_by('-latest_activity')
    context = {'accepted_SP_submissions': accepted_SP_submissions}
    return render(request, 'journals/scipost_physics_accepted.html', context)


def upload_proofs(request):
    """ 
    Called by a member of the Production Team.
    Upload the production version .pdf of a submission.
    """
    return render(request, 'journals/upload_proofs.html')


@permission_required('scipost.can_publish_accepted_submission', raise_exception=True)
@transaction.atomic
def publish_accepted_submission(request):
    return render(request, 'journals/publish_accepted_submission.html')
