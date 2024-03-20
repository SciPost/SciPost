__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, register_converter

from colleges.converters import CollegeSlugConverter
from submissions.converters import IdentifierConverter

app_name = "edadmin"

register_converter(IdentifierConverter, "identifier")
register_converter(CollegeSlugConverter, "college")


urlpatterns = [
    path("", include("edadmin.urls.base")),
    path(
        "incoming/",
        include("edadmin.urls.incoming", namespace="incoming"),
    ),
    path(
        "preassignment/",
        include("edadmin.urls.preassignment", namespace="preassignment"),
    ),
    path(
        "incoming/",
        include("edadmin.urls.subtabs", namespace="subtabs"),
    ),
    path(
        "monitor/",
        include("edadmin.urls.monitor", namespace="monitor"),
    ),
]
