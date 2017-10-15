from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

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
