__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views


app_name = "careers"

urlpatterns = [
    path(  # /careers/job_openings/add
        "job_openings/add",
        views.JobOpeningCreateView.as_view(),
        name="job_opening_create",
    ),
    path(  # /careers/job_openings/update
        "job_openings/<slug:slug>/update",
        views.JobOpeningUpdateView.as_view(),
        name="job_opening_update",
    ),
    path(  # /careers/job_openings
        "job_openings", views.JobOpeningListView.as_view(), name="job_openings"
    ),
    path(  # /careers/job_openings/<slug>
        "job_openings/<slug:slug>",
        views.JobOpeningDetailView.as_view(),
        name="job_opening_detail",
    ),
    path(  # /careers/job_openings/<slug>/apply
        "job_openings/<slug:slug>/apply",
        views.JobOpeningApplyView.as_view(),
        name="job_opening_apply",
    ),
    path(  # /careers/job_application/<uuid>/verify
        "job_application/<uuid:uuid>/verify",
        views.job_application_verify,
        name="job_application_verify",
    ),
    path(  # /careers/job_application/<uuid>
        "job_application/<uuid:uuid>",
        views.JobApplicationDetailView.as_view(),
        name="job_application_detail",
    ),
]
