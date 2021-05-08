__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, register_converter

from . import views
from .converters import Crossref_DOI_converter

app_name='affiliates'

register_converter(Crossref_DOI_converter, 'doi')

urlpatterns = [
    path( # /affiliates/journals
        'journals',
        views.AffiliateJournalListView.as_view(),
        name='journals'
    ),
    path( # /affiliates/journals/<slug>
        'journals/<slug:slug>',
        views.AffiliateJournalDetailView.as_view(),
        name='journal_detail'
    ),
    path( # /affiliates/publications/<doi:doi>
        'publications/<doi:doi>',
        views.AffiliatePublicationDetailView.as_view(),
        name='publication_detail'
    ),
]
