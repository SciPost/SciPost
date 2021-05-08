__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import AffiliateJournal, AffiliatePublication


class AffiliateJournalListView(ListView):
    model = AffiliateJournal


class AffiliateJournalDetailView(DetailView):
    model = AffiliateJournal


class AffiliatePublicationDetailView(DetailView):
    model = AffiliatePublication
    slug_field = 'doi'
    slug_url_kwarg = 'doi'
