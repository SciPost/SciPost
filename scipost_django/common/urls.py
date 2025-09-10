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
    ),
    path(
        "hx_dynsel/select_option/<int:content_type_id>/<int:object_id>",
        views.HXDynselSelectOptionView.as_view(),
        name="hx_dynsel_select_option",
    ),
    path(
        "hx/celery/task/<uuid:task_id>/status",
        views.HXCeleryTaskStatusView.as_view(),
        name="hx_celery_task_status",
    ),
]
