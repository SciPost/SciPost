__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from profiles.forms import ProfileSelectForm

from .models import Series, Collection


class SeriesListView(ListView):
    """
    List view for Series.
    """
    model = Series


class SeriesDetailView(DetailView):
    """
    Detail view for a Series.
    """
    model = Series


class CollectionDetailView(DetailView):
    """
    Detail view for a Collection.
    """
    model = Collection

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['expected_author_form'] = ProfileSelectForm()
        return context


@permission_required('scipost.can_manage_series')
def collection_add_expected_author(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    expected_author_form=ProfileSelectForm(request.POST or None)
    if expected_author_form.is_valid():
        collection.expected_authors.add(expected_author_form.cleaned_data['profile'])
        collection.save()
    return redirect(collection.get_absolute_url())


@permission_required('scipost.can_manage_series')
def collection_remove_expected_author(request, slug, profile_id):
    collection = get_object_or_404(Collection, slug=slug)
    collection.expected_authors.remove(profile_id)
    collection.save()
    return redirect(collection.get_absolute_url())
