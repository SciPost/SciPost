__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path
from . import views

from rest_framework import routers


# colleges
from colleges.api.viewsets import FellowshipPublicAPIViewSet

# journals
from journals.api.viewsets import (
    PublicationPublicAPIViewSet,
    PublicationPublicSearchAPIViewSet,
    PubFracPublicAPIViewSet,
)

# submissions
from submissions.api.viewsets import (
    SubmissionPublicAPIViewSet,
    SubmissionPublicSearchAPIViewSet,
)

# organizations
from organizations.api.viewsets import (
    OrganizationPublicAPIViewSet,
    OrganizationNAPViewSet,
)

# finances
from finances.api.viewsets import (
    SubsidyFinAdminAPIViewSet,
    SubsidyPublicAPIViewSet,
    SubsidyPaymentPrivateAPIViewSet,
)


# Next two: old style, to be deprecated:
from conflicts.viewsets import ConflictOfInterestViewSet
from news.viewsets import NewsItemViewSet

# Utilities
from api.views.omniauth import OmniAuthUserInfoView
import api.views.search as search_views


app_name = "api"


router = routers.SimpleRouter()

# search (Vue-based) routes
router.register(
    "search/publications",
    PublicationPublicSearchAPIViewSet,
    basename="search_publications",
)
router.register(
    "search/submissions",
    SubmissionPublicSearchAPIViewSet,
    basename="search_submissions",
)

#############################
# publicly-accessible routes
#############################

# colleges
router.register("colleges/fellowships", FellowshipPublicAPIViewSet)


# journals
router.register("publications", PublicationPublicAPIViewSet)
router.register("pubfracs", PubFracPublicAPIViewSet)

# submissions
router.register("submissions", SubmissionPublicAPIViewSet)

# organizations
router.register("organizations", OrganizationPublicAPIViewSet)
router.register("nap", OrganizationNAPViewSet, basename="organization_nap")

# finances
router.register(
    "finadmin/subsidies", SubsidyFinAdminAPIViewSet, basename="subsidies_finadmin"
)
router.register("subsidies/payments", SubsidyPaymentPrivateAPIViewSet)
router.register("subsidies", SubsidyPublicAPIViewSet)

# Next two: old style, to be deprecated:
router.register(r"news", NewsItemViewSet)
router.register(r"conflicts", ConflictOfInterestViewSet)


urlpatterns = [
    path("", views.APIView.as_view(), name="api"),
    *router.urls,
    path(  # /api/omniauth/userinfo/, for SciPost as GitLab/OmniAuth authorization server
        "omniauth/userinfo/", OmniAuthUserInfoView.as_view(), name="omniauth_userinfo"
    ),
    path(  # /api/available_search_tabs/
        "available_search_tabs/",
        search_views.available_search_tabs,
        name="available_search_tabs",
    ),
]
