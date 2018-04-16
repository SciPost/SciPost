__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import CreateView, UpdateView

from .forms import ProceedingsForm
from .models import Proceedings


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def proceedings(request):
    """
    List all Proceedings
    """
    context = {
        'proceedings': Proceedings.objects.all()
    }
    return render(request, 'proceedings/proceedings.html', context)


@login_required
@permission_required('scipost.can_manage_college_composition', raise_exception=True)
def proceedings_details(request, id):
    """
    Show Proceedings details
    """
    proceedings = get_object_or_404(Proceedings, id=id)
    context = {
        'proceedings': proceedings
    }
    return render(request, 'proceedings/proceedings_details.html', context)


class ProceedingsAddView(CreateView):
    models = Proceedings
    form_class = ProceedingsForm
    template_name = 'proceedings/proceedings_add.html'


class ProceedingsUpdateView(UpdateView):
    models = Proceedings
    form_class = ProceedingsForm
    template_name = 'proceedings/proceedings_edit.html'

    def get_object(self):
        return get_object_or_404(Proceedings, id=self.kwargs['id'])
