__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.urls import re_path
from . import views

app_name = "merger"

urlpatterns = [
    re_path(
        r"^(?P<content_type>[^/]+)/duplicates(?:/(?P<group>[^/]+))?(?:/(?P<object_a_pk>\d+)/(?P<object_b_pk>\d+))?/?$",
        views.PotentialDuplicatesView.as_view(),
        name="duplicates",
    ),
]
