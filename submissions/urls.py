from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Submissions
    url(r'^$', views.submissions, name='submissions'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^sub_and_ref_procedure$', TemplateView.as_view(template_name='submissions/sub_and_ref_procedure.html'), name='sub_and_ref_procedure'),
    #url(r'^submission/(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^submit_manuscript$', views.submit_manuscript, name='submit_manuscript'),
    url(r'^submit_manuscript_ack$', TemplateView.as_view(template_name='submissions/submit_manuscript_ack.html'), name='submit_manuscript_ack'),
    url(r'^assign_submissions$', views.assign_submissions, name='assign_submissions'),
    url(r'^assign_submission_ack/(?P<submission_id>[0-9]+)$', views.assign_submission_ack, name='assign_submission_ack'),
    url(r'^accept_or_decline_assignments$', views.accept_or_decline_assignments, name='accept_or_decline_assignments'),
    url(r'^accept_or_decline_assignment_ack/(?P<assignment_id>[0-9]+)$', views.accept_or_decline_assignment_ack, name='accept_or_decline_assignment_ack'),
    url(r'^editorial_page/(?P<submission_id>[0-9]+)$', views.editorial_page, name='editorial_page'),
    url(r'^select_referee/(?P<submission_id>[0-9]+)$', views.select_referee, name='select_referee'),
    url(r'^send_refereeing_invitation/(?P<submission_id>[0-9]+)/(?P<contributor_id>[0-9]+)$', views.send_refereeing_invitation, name='send_refereeing_invitation'),
    url(r'^accept_or_decline_ref_invitations$', views.accept_or_decline_ref_invitations, name='accept_or_decline_ref_invitations'),
    url(r'^accept_or_decline_ref_invitation/(?P<invitation_id>[0-9]+)$', views.accept_or_decline_ref_invitation_ack, name='accept_or_decline_ref_invitation_ack'),
    # Reports
    url(r'^submit_report/(?P<submission_id>[0-9]+)$', views.submit_report, name='submit_report'),
    url(r'^submit_report_ack$', TemplateView.as_view(template_name='submissions/submit_report_ack.html'), name='submit_report_ack'),
    url(r'^vet_submitted_reports$', views.vet_submitted_reports, name='vet_submitted_reports'),
    url(r'^vet_submitted_report_ack/(?P<report_id>[0-9]+)$', views.vet_submitted_report_ack, name='vet_submitted_report_ack'),
]
