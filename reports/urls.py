from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Reports
    url(r'^submit_report/(?P<submission_id>[0-9]+)$', views.submit_report, name='submit_report'),
    url(r'^submit_report_ack$', views.submit_report_ack, name='submit_report_ack'),
    url(r'^vet_submitted_reports$', views.vet_submitted_reports, name='vet_submitted_reports'),
    url(r'^vet_submitted_report_ack/(?P<report_id>[0-9]+)$', views.vet_submitted_report_ack, name='vet_submitted_report_ack'),

]
