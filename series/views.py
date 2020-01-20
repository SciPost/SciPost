__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

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
