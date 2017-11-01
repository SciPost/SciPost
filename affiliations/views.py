from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404

from .forms import AffiliationMergeForm
from .models import Affiliation


class AffiliationListView(ListView):
    model = Affiliation
    paginate_by = 100


class AffiliationUpdateView(UpdateView):
    model = Affiliation
    pk_url_kwarg = 'affiliation_id'
    fields = [
        'name',
        'acronym',
        'country',
    ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['merge_form'] = AffiliationMergeForm()
        return context

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, 'Affiliation saved')
        return super().form_valid(*args, **kwargs)


def merge_affiliations(request, affiliation_id):
    """
    Merge Affiliation (affiliation_id) into the Affliation chosen in the form.
    """
    affiliation = get_object_or_404(Affiliation, id=affiliation_id)
    form = AffiliationMergeForm(request.POST or None, instance=affiliation)
    if form.is_valid():
        form.save()
        messages.success(request, 'Affiliation {a} merged into {b}'.format(
            a=form.cleaned_data.get('affiliation', '?'), b=affiliation))

    return redirect(reverse('affiliations:affiliation_details', args=(affiliation.id,)))
