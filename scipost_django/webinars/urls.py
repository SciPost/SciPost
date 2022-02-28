__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "webinars"


urlpatterns = [
    path(
        "<slug:slug>",
        views.webinar_detail,
        name="webinar_detail",
    ),
    path(
        "<slug:slug>/register",
        views.webinar_register,
        name="webinar_register",
    ),
]
