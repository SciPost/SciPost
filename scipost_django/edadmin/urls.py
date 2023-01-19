__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views

app_name = "edadmin"


urlpatterns = [
    path("", views.edadmin, name="edadmin"),
]
