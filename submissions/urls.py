from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Submissions
    url(r'^$', views.SubmissionListView.as_view(), name='submissions'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]{1,3})/$',
        views.SubmissionListView.as_view(), name='browse'),
    url(r'^sub_and_ref_procedure$',
        TemplateView.as_view(template_name='submissions/sub_and_ref_procedure.html'),
        name='sub_and_ref_procedure'),
    url(r'^author_guidelines$',
        TemplateView.as_view(template_name='submissions/author_guidelines.html'),
        name='author_guidelines'),
    url(r'^(?P<arxiv_identifier_wo_vn_nr>[0-9]{4,}.[0-9]{5,})/$', views.submission_detail_wo_vn_nr,
        name='submission_wo_vn_nr'),
    url(r'^(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/$',
        views.submission_detail, name='submission'),
    url(r'^(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/reports/(?P<report_nr>[0-9]+)/pdf$',
        views.report_detail_pdf, name='report_detail_pdf'),
    url(r'^(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/reports/pdf$',
        views.submission_refereeing_package_pdf, name='refereeing_package_pdf'),

    # Editorial Administration
    url(r'^admin$', views.EditorialSummaryView.as_view(), name='admin'),
    url(r'^admin/treated$', views.treated_submissions_list, name='treated_submissions_list'),
    url(r'^admin/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/reports/compile$',
        views.treated_submission_pdf_compile, name='treated_submission_pdf_compile'),
    url(r'^admin/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/plagiarism$',
        views.PlagiarismView.as_view(), name='plagiarism'),
    url(r'^admin/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/plagiarism/report$',
        views.PlagiarismReportPDFView.as_view(), name='plagiarism_report'),
    url(r'^admin/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/recommendations/(?P<rec_id>[0-9]+)$',
        views.EICRecommendationView.as_view(), name='eic_recommendation_detail'),
    url(r'^admin/events/latest$', views.latest_events, name='latest_events'),
    url(r'^admin/reports$', views.reports_accepted_list, name='reports_accepted_list'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),

    url(r'^submit_manuscript$', views.RequestSubmission.as_view(), name='submit_manuscript'),
    url(r'^submit_manuscript/prefill$', views.prefill_using_arxiv_identifier,
        name='prefill_using_identifier'),
    url(r'^pool$', views.pool, name='pool'),
    url(r'^submissions_by_status/(?P<status>[a-zA-Z_]+)$',
        views.submissions_by_status, name='submissions_by_status'),
    url(r'^add_remark/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.add_remark, name='add_remark'),

    # Assignment of Editor-in-charge
    url(r'^assign_submission/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.assign_submission, name='assign_submission'),
    url(r'^assign_submission_ack/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.assign_submission_ack, name='assign_submission_ack'),
    url(r'^accept_or_decline_assignment_ack/(?P<assignment_id>[0-9]+)$',
        views.accept_or_decline_assignment_ack, name='accept_or_decline_assignment_ack'),
    url(r'^volunteer_as_EIC/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.volunteer_as_EIC, name='volunteer_as_EIC'),
    url(r'^assignment_failed/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.assignment_failed, name='assignment_failed'),
    # Editorial workflow and refereeing
    url(r'^editorial_workflow$', views.editorial_workflow, name='editorial_workflow'),
    url(r'^assignments$', views.assignments, name='assignments'),
    url(r'^editorial_page/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.editorial_page, name='editorial_page'),
    url(r'^select_referee/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.select_referee, name='select_referee'),
    url(r'^recruit_referee/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.recruit_referee, name='recruit_referee'),
    url(r'^send_refereeing_invitation/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<contributor_id>[0-9]+)$',
        views.send_refereeing_invitation, name='send_refereeing_invitation'),
    url(r'^accept_or_decline_ref_invitations/$',
        views.accept_or_decline_ref_invitations, name='accept_or_decline_ref_invitations'),
    url(r'^accept_or_decline_ref_invitation/(?P<invitation_id>[0-9]+)$',
        views.accept_or_decline_ref_invitation_ack, name='accept_or_decline_ref_invitation_ack'),
    url(r'^decline_ref_invitation/(?P<invitation_key>.+)$',
        views.decline_ref_invitation, name='decline_ref_invitation'),
    url(r'^ref_invitation_reminder/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<invitation_id>[0-9]+)$', views.ref_invitation_reminder, name='ref_invitation_reminder'),
    url(r'^cancel_ref_invitation/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<invitation_id>[0-9]+)$',
        views.cancel_ref_invitation, name='cancel_ref_invitation'),
    url(r'^extend_refereeing_deadline/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<days>[0-9]+)$',
        views.extend_refereeing_deadline, name='extend_refereeing_deadline'),
    url(r'^set_refereeing_deadline/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.set_refereeing_deadline, name='set_refereeing_deadline'),
    url(r'^close_refereeing_round/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.close_refereeing_round, name='close_refereeing_round'),
    url(r'^refereeing_overview$', views.refereeing_overview, name='refereeing_overview'),
    url(r'^communication/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<comtype>[a-zA-Z]{4,})$',
        views.communication, name='communication'),
    url(r'^communication/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/(?P<comtype>[a-zA-Z]{4,})/(?P<referee_id>[0-9]+)$',
        views.communication, name='communication'),
    url(r'^eic_recommendation/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})$',
        views.eic_recommendation, name='eic_recommendation'),
    url(r'^cycle/(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/submit$',
        views.cycle_form_submit, name='cycle_confirmation'),

    # Reports
    url(r'^(?P<arxiv_identifier_w_vn_nr>[0-9]{4,}.[0-9]{5,}v[0-9]{1,2})/reports/submit$',
        views.submit_report, name='submit_report'),
    url(r'^reports/vet$', views.vet_submitted_reports_list, name='vet_submitted_reports_list'),
    url(r'^reports/(?P<report_id>[0-9]+)/vet$', views.vet_submitted_report,
        name='vet_submitted_report'),

    # Voting
    url(r'^prepare_for_voting/(?P<rec_id>[0-9]+)$', views.prepare_for_voting, name='prepare_for_voting'),
    url(r'^vote_on_rec/(?P<rec_id>[0-9]+)$', views.vote_on_rec, name='vote_on_rec'),
    url(r'^remind_Fellows_to_vote$', views.remind_Fellows_to_vote,
        name='remind_Fellows_to_vote'),
    # Editorial Administration
    url(r'fix_College_decision/(?P<rec_id>[0-9]+)$', views.fix_College_decision,
        name='fix_College_decision'),
]
