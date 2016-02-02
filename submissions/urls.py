from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Submissions
    url(r'^$', views.submissions, name='submissions'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^sub_and_ref_procedure$', views.sub_and_ref_procedure, name='sub_and_ref_procedure'),
    url(r'^submission/(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^submit_manuscript$', views.submit_manuscript, name='submit_manuscript'),
    url(r'^submit_manuscript_ack$', views.submit_manuscript_ack, name='submit_manuscript_ack'),
    url(r'^process_new_submissions$', views.process_new_submissions, name='process_new_submissions'),
    #url(r'^no_new_submission_to_process$', views.no_new_submission_to_process, name='no_new_submission_to_process'),
    url(r'^process_new_submission_ack/(?P<submission_id>[0-9]+)$', views.process_new_submission_ack, name='process_new_submission_ack'),
    # Reports
    url(r'^submit_report/(?P<submission_id>[0-9]+)$', views.submit_report, name='submit_report'),
    url(r'^submit_report_ack$', views.submit_report_ack, name='submit_report_ack'),
    url(r'^vet_submitted_reports$', views.vet_submitted_reports, name='vet_submitted_reports'),
    #url(r'^no_report_to_vet$', views.no_report_to_vet, name='no_report_to_vet'),
    url(r'^vet_submitted_report_ack/(?P<report_id>[0-9]+)$', views.vet_submitted_report_ack, name='vet_submitted_report_ack'),
]
