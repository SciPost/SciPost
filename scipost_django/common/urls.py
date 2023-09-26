__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "common"

urlpatterns = [
    path(
        "empty",
        views.empty,
        name="empty",
    )
]
