__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import include, path

from rest_framework import routers

from journals.viewsets import PublicationViewSet
from organizations.api.viewsets import OrganizationViewSet, OrganizationNAPViewSet
from submissions.viewsets import SubmissionViewSet

# Next two: old style, to be deprecated:
from conflicts.viewsets import ConflictOfInterestViewSet
from news.viewsets import NewsItemViewSet

from . import views

app_name = 'api'


router = routers.SimpleRouter()

# journals
router.register('publications', PublicationViewSet)

# organizations
router.register('organizations', OrganizationViewSet)
router.register('nap/organizations', OrganizationNAPViewSet)

# submissions
router.register('submissions', SubmissionViewSet)

# Next two: old style, to be deprecated:
router.register(r'news', NewsItemViewSet)
router.register(r'conflicts', ConflictOfInterestViewSet)


urlpatterns = router.urls


urlpatterns += [

    path( # /api/omniauth/userinfo/, for SciPost as GitLab/OmniAuth authorization server
        'omniauth/userinfo/',
        views.OmniAuthUserInfoView.as_view(),
        name='omniauth_userinfo'
    ),
    path('finances/', include('finances.api.urls')),
    path('journals/', include('journals.api.urls')),
    path('organizations/', include('organizations.api.urls')),

]
