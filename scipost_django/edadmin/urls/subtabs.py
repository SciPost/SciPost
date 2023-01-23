__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, register_converter

from ..converters import SubmissionStageSlugConverter
from ..views import subtabs

app_name="subtabs"


urlpatterns = [
    path(
        "<identifier:identifier_w_vn_nr>/",
        include([
            path(
                "subtab/<slug:subtab>",
                subtabs._hx_submission_edadmin_subtab,
                name="_hx_submission_edadmin_subtab",
            ),
        ])
    ),
]
