copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from organizations.api import views as api_views


urlpatterns = [

    path( # /api/organizations/
        '',
        api_views.OrganizationListAPIView.as_view(),
        name='organizations'
    ),
    path( # /api/organizations/<int:pk>
        '<int:pk>',
        api_views.OrganizationRetrieveAPIView.as_view(),
        name='organization-detail'
    ),

]
