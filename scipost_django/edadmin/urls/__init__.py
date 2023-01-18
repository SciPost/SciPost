__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

app_name = "edadmin"


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
]
