__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views


app_name = 'careers'

urlpatterns = [

    path( # /careers/job_openings/add
        'job_openings/add',
        views.JobOpeningCreateView.as_view(),
        name='jobopening_create'
    ),
    path( # /careers/job_openings/update
        'job_openings/<slug:slug>/update',
        views.JobOpeningUpdateView.as_view(),
        name='jobopening_update'
    ),
    path( # /careers/job_openings
        'job_openings',
        views.JobOpeningListView.as_view(),
        name='jobopenings'
    ),
    path( # /careers/job_openings/<slug>
        'job_openings/<slug:slug>',
        views.JobOpeningDetailView.as_view(),
        name='jobopening_detail'
    ),
    path( # /careers/job_openings/<slug>/apply
        'job_openings/<slug:slug>/apply',
        views.JobOpeningApplyView.as_view(),
        name='jobopening_apply'
    ),
    path( # /careers/job_application/<uuid>/verify
        'job_application/<uuid:uuid>/verify',
        views.jobapplication_verify,
        name='jobapplication_verify'
    ),
    path( # /careers/job_application/<uuid>
        'job_application/<uuid:uuid>',
        views.JobApplicationDetailView.as_view(),
        name='jobapplication_detail'
    ),
]
