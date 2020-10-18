__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from finances.api import views as api_views


urlpatterns = [

    path ( # /api/finances/subsidies
        'subsidies',
        api_views.SubsidyListAPIView.as_view(),
        name='subsidies'
    ),

]
