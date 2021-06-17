copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from rest_framework import routers

#from organizations.api import views as api_views
from . import views as api_views
from . import viewsets as api_viewsets


router = routers.SimpleRouter()

# OrganizationNAPViewSet before OrganizationViewSet, to prevent 404
router.register('nap', api_viewsets.OrganizationNAPViewSet)
router.register('', api_viewsets.OrganizationViewSet)


urlpatterns = router.urls

urlpatterns += [

    path( # /api/organizations/<int:pk>/balance
        '<int:pk>/balance',
        api_views.OrganizationBalanceAPIView.as_view(),
        name='organization-balance',
    )
]
