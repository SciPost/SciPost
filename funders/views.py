import requests
import json

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView
from django.shortcuts import get_object_or_404, render, redirect

from .models import Funder, Grant
from .forms import FunderRegistrySearchForm, FunderForm, GrantForm

from scipost.mixins import PermissionsMixin


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def funders(request):
    funders = Funder.objects.all()
    form = FunderRegistrySearchForm()
    grants = Grant.objects.all()
    grant_form = GrantForm(request=request)
    context = {'form': form, 'funders': funders,
               'grants': grants, 'grant_form': grant_form}
    return render(request, 'funders/funders.html', context)


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def query_crossref_for_funder(request):
    """
    Checks Crossref's Fundref Registry for an entry
    corresponding to the funder name being looked for.
    If found, creates a funders.Funder instance.
    """
    form = FunderRegistrySearchForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        queryurl = 'http://api.crossref.org/funders?query=%s' % form.cleaned_data['name']
        query = requests.get(queryurl)
        response = json.loads(query.text)
        context['response_headers'] = query.headers
        context['response_text'] = query.text
        context['response'] = response
        context['funder_form'] = FunderForm()
    return render(request, 'funders/query_crossref_for_funder.html', context)


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def add_funder(request):
    form = FunderForm(request.POST or None)
    if form.is_valid():
        funder = form.save()
        messages.success(request, ('<h3>Funder %s successfully created</h3>') %
                         str(funder))
    elif form.has_changed():
        messages.warning(request, 'The form was invalidly filled.')
    return redirect(reverse('funders:funders'))


def funder_publications(request, funder_id):
    """
    See details of specific Funder (publicly accessible).
    """
    funder = get_object_or_404(Funder, id=funder_id)
    context = {'funder': funder}
    return render(request, 'funders/funder_details.html', context)


class HttpRefererMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data.get('http_referer'):
            self.success_url = form.cleaned_data['http_referer']
        return super().form_valid(form)


@method_decorator(transaction.atomic, name='dispatch')
class CreateGrantView(PermissionsMixin, HttpRefererMixin, CreateView):
    """
    Create a Grant in a separate window which may also be used by Production Supervisors.
    """
    permission_required = 'scipost.can_create_grants'
    model = Grant
    form_class = GrantForm
    success_url = reverse_lazy('funders:funders')
