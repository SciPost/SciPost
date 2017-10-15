from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def proceedings(request):
    context = {}
    return render(request, 'proceedings/index.html', context)
