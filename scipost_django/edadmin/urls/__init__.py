__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import base

app_name = "edadmin"


urlpatterns = [
    path("", base.edadmin, name="edadmin"),
    path("incoming/", include("edadmin.urls.incoming")),
]
