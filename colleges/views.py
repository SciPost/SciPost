from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import FellowshipForm, FellowshipTerminateForm, FellowshipRemoveSubmissionForm,\
    FellowshipAddSubmissionForm, AddFellowshipForm
from .models import Fellowship


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowships(request):
    """
    List all fellowships to be able to edit them, or create new ones.
    """
    fellowships = Fellowship.objects.active()

    context = {
        'fellowships': fellowships
    }
    return render(request, 'colleges/fellowships.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def fellowship_detail(request, id):
    """
    View details of a specific fellowship
    """
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
def fellowship_remove_submission(request, id, arxiv_identifier_w_vn_nr):
    """
    Remove Submission from the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    submission = get_object_or_404(fellowship.pool.all(),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    form = FellowshipRemoveSubmissionForm(request.POST or None,
                                          submission=submission, instance=fellowship)

    if form.is_valid() and request.POST:
        form.save()
        messages.success(request, 'Submission {sub} removed from Fellowship.'.format(
            sub=arxiv_identifier_w_vn_nr))
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
    """
    Add Submission to the pool of a Fellowship.
    """
    fellowship = get_object_or_404(Fellowship, id=id)
    form = FellowshipAddSubmissionForm(request.POST or None, instance=fellowship)

    if form.is_valid():
        form.save()
        messages.success(request, 'Submission {submission} added to Fellowship.'.format(
            submission=form.cleaned_data['submission'].arxiv_identifier_w_vn_nr))
        return redirect(fellowship.get_absolute_url())

    context = {
        'fellowship': fellowship,
        'form': form,
    }
    return render(request, 'colleges/fellowship_submission_add.html', context)
