__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import monitor as monitor_views

app_name = "edadmin_monitor"


urlpatterns = [
    path(
        "fellow_activity",
        monitor_views.fellow_activity,
        name="fellow_activity",
    ),
    path(
        "<int:fellowship_id>/_hx_fellow_stage_assignment_appraisals_table",
        monitor_views._hx_fellow_stage_assignment_appraisals_table,
        name="_hx_fellow_stage_assignment_appraisals_table",
    ),
]
