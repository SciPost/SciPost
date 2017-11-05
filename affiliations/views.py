from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404

from .forms import InstituteMergeForm
from .models import Institute


@method_decorator(permission_required('scipost.can_manage_affiliations'), name='dispatch')
class InstituteListView(ListView):
    model = Institute
    paginate_by = 100


@method_decorator(permission_required('scipost.can_manage_affiliations'), name='dispatch')
class InstituteUpdateView(UpdateView):
    model = Institute
    pk_url_kwarg = 'institute_id'
    fields = [
        'name',
        'acronym',
        'country',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['merge_form'] = InstituteMergeForm()
        return context

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, 'Institute saved')
        return super().form_valid(*args, **kwargs)


@permission_required('scipost.can_manage_affiliations')
def merge_institutes(request, institute_id):
    """
    Merge Affiliation (affiliation_id) into the Affliation chosen in the form.
    """
    institute = get_object_or_404(Institute, id=institute_id)
    form = InstituteMergeForm(request.POST or None, instance=institute)
    if form.is_valid():
        form.save()
        messages.success(request, 'Institute {a} merged into {b}'.format(
            a=form.cleaned_data.get('institute', '?'), b=institute))

    return redirect(reverse('affiliations:institute_details', args=(institute.id,)))
