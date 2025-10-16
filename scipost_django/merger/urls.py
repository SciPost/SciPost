__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.urls import re_path
from . import views

app_name = "merger"

urlpatterns = [
    # Needs to be above duplicates because "invalidate" would be treated as a group
    re_path(
        r"^(?P<content_type>[^/]+)/duplicates/invalidate(?:/(?P<object_a_pk>\d+)/(?P<object_b_pk>\d+))?/?$",
        views.HXNonDuplicateMarkCreateView.as_view(),
        name="mark_non_duplicate",
    ),
    re_path(
        r"^(?P<content_type>[^/]+)/duplicates(?:/(?P<group>[^/]+))?(?:/(?P<object_a_pk>\d+)/(?P<object_b_pk>\d+))?/?$",
        views.PotentialDuplicatesView.as_view(),
        name="duplicates",
    ),
    re_path(
        r"^(?P<content_type>[^/]+)/compare(?:/(?P<object_a_pk>\d+)/(?P<object_b_pk>\d+))?/?$",
        views.HXCompareView.as_view(),
        name="compare",
    ),
]
