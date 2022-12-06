__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, register_converter

from ..converters import SubmissionStageSlugConverter
from ..views import base

app_name = "edadmin"


register_converter(SubmissionStageSlugConverter, "stage")

urlpatterns = [
    path("", base.edadmin, name="edadmin"),
    path(
        "<stage:stage>",
        base._hx_submissions_in_stage,
        name="_hx_submissions_in_stage",
    ),
    path("incoming/", include("edadmin.urls.incoming")),
]
