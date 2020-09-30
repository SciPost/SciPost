__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import include, path

from rest_framework import routers

from conflicts.viewsets import ConflictOfInterestViewSet
from news.viewsets import NewsItemViewSet

from . import views

router = routers.SimpleRouter()
router.register(r'news', NewsItemViewSet)
router.register(r'conflicts', ConflictOfInterestViewSet)

app_name = 'api'


urlpatterns = router.urls


urlpatterns += [

    path( # /api/omniauth/userinfo/, for SciPost as GitLab/OmniAuth authorization server
        'omniauth/userinfo/',
        views.OmniAuthUserInfoView.as_view(),
        name='omniauth_userinfo'
    ),
    path('journals/', include('journals.api.urls')),
    path('organizations/', include('organizations.api.urls')),

]
