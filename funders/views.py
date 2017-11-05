import requests
import json

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render, redirect

from .models import Funder, Grant
from .forms import FunderRegistrySearchForm, FunderForm, GrantForm


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def funders(request):
    funders = Funder.objects.all()
    form = FunderRegistrySearchForm()
    grants = Grant.objects.all()
    grant_form = GrantForm()
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


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def funder_publications(request, funder_id):
    """
    See details of specific Funder.
    """
    funder = get_object_or_404(Funder, id=funder_id)
    context = {'funder': funder}
    return render(request, 'funders/funder_details.html', context)


@permission_required('scipost.can_view_all_funding_info', raise_exception=True)
def add_grant(request):
    grant_form = GrantForm(request.POST or None)
    if grant_form.is_valid():
        grant = grant_form.save()
        messages.success(request, ('<h3>Grant %s successfully added</h3>') %
                         str(grant))
    elif grant_form.has_changed():
        messages.warning(request, 'The form was invalidly filled (grant already exists?).')
    return redirect(reverse('funders:funders'))
