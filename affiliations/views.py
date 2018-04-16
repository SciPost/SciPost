__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404

from .forms import InstitutionMergeForm
from .models import Institution


@method_decorator(permission_required('scipost.can_manage_affiliations'), name='dispatch')
class InstitutionListView(ListView):
    model = Institution
    paginate_by = 100


@method_decorator(permission_required('scipost.can_manage_affiliations'), name='dispatch')
class InstitutionUpdateView(UpdateView):
    model = Institution
    pk_url_kwarg = 'institution_id'
    fields = [
        'name',
        'acronym',
        'country',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['merge_form'] = InstitutionMergeForm()
        return context

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, 'Institution saved')
        return super().form_valid(*args, **kwargs)


@permission_required('scipost.can_manage_affiliations')
def merge_institutions(request, institution_id):
    """
    Merge Affiliation (affiliation_id) into the Affliation chosen in the form.
    """
    institution = get_object_or_404(Institution, id=institution_id)
    form = InstitutionMergeForm(request.POST or None, instance=institution)
    if form.is_valid():
        form.save()
        messages.success(request, 'Institution {a} merged into {b}'.format(
            a=form.cleaned_data.get('institution', '?'), b=institution))

    return redirect(reverse('affiliations:institution_details', args=(institution.id,)))
