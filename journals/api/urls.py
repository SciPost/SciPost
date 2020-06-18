__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from journals.api import views as api_views


urlpatterns = [

    path( # /api/journals/publications
        'publications',
        api_views.PublicationListAPIView.as_view(),
        name='publications'
    ),
    path( # /api/journals/publications/<doi_label>
        'publications/<str:doi_label>',
        api_views.PublicationRetrieveAPIView.as_view(),
        name='publication-detail'
    ),

    path( # /api/journals/pubfractions
        'pubfractions',
        api_views.OrgPubFractionListAPIView.as_view(),
        name='pubfractions'
    ),

]
