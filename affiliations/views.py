# from django.shortcuts import render
from django.views.generic.list import ListView

from .models import Affiliation


class AffiliationListView(ListView):
    model = Affiliation
    paginate_by = 100
