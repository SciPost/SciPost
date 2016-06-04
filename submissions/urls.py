from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Submissions
    url(r'^$', views.submissions, name='submissions'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^sub_and_ref_procedure$', TemplateView.as_view(template_name='submissions/sub_and_ref_procedure.html'), name='sub_and_ref_procedure'),
    url(r'^author_guidelines$', TemplateView.as_view(template_name='submissions/author_guidelines.html'), name='author_guidelines'),
    url(r'^(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^prefill_using_identifier$', views.prefill_using_identifier, name='prefill_using_identifier'),
    url(r'^submit_manuscript$', views.submit_manuscript, name='submit_manuscript'),
    url(r'^submit_manuscript_ack$', TemplateView.as_view(template_name='submissions/submit_manuscript_ack.html'), name='submit_manuscript_ack'),
    url(r'^pool$', views.pool, name='pool'),
    # Assignment of Editor-in-charge
    url(r'^assign_submission/(?P<submission_id>[0-9]+)$', views.assign_submission, name='assign_submission'),
    url(r'^assign_submission_ack/(?P<submission_id>[0-9]+)$', views.assign_submission_ack, name='assign_submission_ack'),
    url(r'^accept_or_decline_assignment_ack/(?P<assignment_id>[0-9]+)$', views.accept_or_decline_assignment_ack, name='accept_or_decline_assignment_ack'),
    url(r'^volunteer_as_EIC/(?P<submission_id>[0-9]+)$', views.volunteer_as_EIC, name='volunteer_as_EIC'),
    url(r'^assignment_failed/(?P<submission_id>[0-9]+)$', views.assignment_failed, name='assignment_failed'),
    # Editorial workflow and refereeing
    url(r'^editorial_workflow$', views.editorial_workflow, name='editorial_workflow'),
    url(r'^editorial_page/(?P<submission_id>[0-9]+)$', views.editorial_page, name='editorial_page'),
    url(r'^select_referee/(?P<submission_id>[0-9]+)$', views.select_referee, name='select_referee'),
    url(r'^recruit_referee/(?P<submission_id>[0-9]+)$', views.recruit_referee, name='recruit_referee'),
    url(r'^send_refereeing_invitation/(?P<submission_id>[0-9]+)/(?P<contributor_id>[0-9]+)$', views.send_refereeing_invitation, name='send_refereeing_invitation'),
    url(r'^accept_or_decline_ref_invitations$', views.accept_or_decline_ref_invitations, name='accept_or_decline_ref_invitations'),
    url(r'^accept_or_decline_ref_invitation/(?P<invitation_id>[0-9]+)$', views.accept_or_decline_ref_invitation_ack, name='accept_or_decline_ref_invitation_ack'),
    url(r'^ref_invitation_reminder/(?P<submission_id>[0-9]+)/(?P<invitation_id>[0-9]+)$', views.ref_invitation_reminder, name='ref_invitation_reminder'),
    url(r'^extend_refereeing_deadline/(?P<submission_id>[0-9]+)/(?P<days>[0-9]+)$', views.extend_refereeing_deadline, name='extend_refereeing_deadline'),
    url(r'^close_refereeing_round/(?P<submission_id>[0-9]+)$', views.close_refereeing_round, name='close_refereeing_round'),
    url(r'^communication/(?P<submission_id>[0-9]+)/(?P<comtype>[a-zA-Z]{4,})$', views.communication, name='communication'),
    url(r'^communication/(?P<submission_id>[0-9]+)/(?P<comtype>[a-zA-Z]{4,})/(?P<referee_id>[0-9]+)$', views.communication, name='communication'),
    url(r'^eic_recommendation/(?P<submission_id>[0-9]+)$', views.eic_recommendation, name='eic_recommendation'),
    # Reports
    url(r'^submit_report/(?P<submission_id>[0-9]+)$', views.submit_report, name='submit_report'),
    url(r'^submit_report_ack$', TemplateView.as_view(template_name='submissions/submit_report_ack.html'), name='submit_report_ack'),
    url(r'^vet_submitted_reports$', views.vet_submitted_reports, name='vet_submitted_reports'),
    url(r'^vet_submitted_report_ack/(?P<report_id>[0-9]+)$', views.vet_submitted_report_ack, name='vet_submitted_report_ack'),
]
