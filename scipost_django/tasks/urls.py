__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
from django.views.generic import TemplateView

from . import views

app_name = "tasks"

urlpatterns = [
    path("list", views.tasklist, name="tasklist"),
    path("list/new/grouped", views.tasklist_new_grouped, name="tasklist_new_grouped"),
    path("list/new", views.tasklist_new, name="tasklist_new"),
]
