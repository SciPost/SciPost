__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import include, path

from rest_framework import routers

from journals.api.viewsets import (
    PublicationPublicAPIViewSet,
    PubFractionPublicAPIViewSet
)
from organizations.api.viewsets import (
    OrganizationPublicAPIViewSet,
    OrganizationNAPViewSet
)
from submissions.api.viewsets import SubmissionPublicAPIViewSet

# Next two: old style, to be deprecated:
from conflicts.viewsets import ConflictOfInterestViewSet
from news.viewsets import NewsItemViewSet

from api.views.omniauth import OmniAuthUserInfoView
import api.views.search as search_views


app_name = 'api'


router = routers.SimpleRouter()

# journals
router.register('publications', PublicationPublicAPIViewSet)
router.register('pubfractions', PubFractionPublicAPIViewSet)

# organizations
router.register('organizations', OrganizationPublicAPIViewSet)
router.register('nap', OrganizationNAPViewSet)

# submissions
router.register('submissions', SubmissionPublicAPIViewSet)

# Next two: old style, to be deprecated:
router.register(r'news', NewsItemViewSet)
router.register(r'conflicts', ConflictOfInterestViewSet)


urlpatterns = router.urls


urlpatterns += [

    path( # /api/omniauth/userinfo/, for SciPost as GitLab/OmniAuth authorization server
        'omniauth/userinfo/',
        OmniAuthUserInfoView.as_view(),
        name='omniauth_userinfo'
    ),
    path( # /api/available_search_tabs/
        'available_search_tabs/',
        search_views.available_search_tabs,
        name='available_search_tabs'
    ),
    path('finances/', include('finances.api.urls')),
]
