__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views
from .constants import SUBMISSIONS_NO_VN_REGEX, SUBMISSIONS_COMPLETE_REGEX

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
    url(r'^referee_guidelines$',
        TemplateView.as_view(template_name='submissions/referee_guidelines.html'),
        name='referee_guidelines'),
    url(r'^{regex}/$'.format(regex=SUBMISSIONS_NO_VN_REGEX), views.submission_detail_wo_vn_nr,
        name='submission_wo_vn_nr'),
    url(r'^{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_detail, name='submission'),
    url(r'^{regex}/reports/(?P<report_nr>[0-9]+)/pdf$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.report_detail_pdf, name='report_detail_pdf'),
    url(r'^{regex}/reports/(?P<report_nr>[0-9]+)/attachment$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.report_attachment, name='report_attachment'),
    url(r'^{regex}/reports/pdf$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_refereeing_package_pdf, name='refereeing_package_pdf'),

    # Editorial Administration
    url(r'^admin/treated$', views.treated_submissions_list, name='treated_submissions_list'),
    url(r'^admin/{regex}/prescreening$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PreScreeningView.as_view(), name='do_prescreening'),
    url(r'^admin/{regex}/preassign_editors$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.preassign_editors, name='preassign_editors'),
    url(r'^admin/{regex}/reports/compile$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.treated_submission_pdf_compile, name='treated_submission_pdf_compile'),
    url(r'^admin/{regex}/plagiarism$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PlagiarismView.as_view(), name='plagiarism'),
    url(r'^admin/{regex}/plagiarism/report$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PlagiarismReportPDFView.as_view(), name='plagiarism_report'),
    url(r'^admin/{regex}/recommendations/(?P<rec_id>[0-9]+)$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.EICRecommendationView.as_view(), name='eic_recommendation_detail'),
    url(r'^admin/reports$', views.reports_accepted_list, name='reports_accepted_list'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),

    url(r'^submit_manuscript$', views.RequestSubmission.as_view(), name='submit_manuscript'),
    url(r'^submit_manuscript/prefill$', views.prefill_using_arxiv_identifier,
        name='prefill_using_identifier'),
    url(r'^pool/$', views.pool, name='pool'),
    url(r'^pool/{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX), views.pool, name='pool'),
    url(r'^add_remark/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.add_remark, name='add_remark'),

    # Assignment of Editor-in-charge
    url(r'^assign_submission/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.assign_submission, name='assign_submission'),
    url(r'^pool/assignment_request/(?P<assignment_id>[0-9]+)$',
        views.assignment_request, name='assignment_request'),
    url(r'^pool/{regex}/editorial_assignment/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.editorial_assignment,
        name='editorial_assignment'),
    url(r'^pool/{regex}/editorial_assignment/(?P<assignment_id>[0-9]+)/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.editorial_assignment,
        name='editorial_assignment'),
    url(r'^volunteer_as_EIC/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.volunteer_as_EIC, name='volunteer_as_EIC'),
    url(r'^assignment_failed/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.assignment_failed, name='assignment_failed'),
    # Editorial workflow and refereeing
    url(r'^editorial_workflow$', views.editorial_workflow, name='editorial_workflow'),
    url(r'^assignments$', views.assignments, name='assignments'),
    url(r'^editorial_page/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.editorial_page, name='editorial_page'),
    url(r'^select_referee/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.select_referee, name='select_referee'),
    url(r'^recruit_referee/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.recruit_referee, name='recruit_referee'),
    url(r'^send_refereeing_invitation/{regex}/(?P<contributor_id>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.send_refereeing_invitation, name='send_refereeing_invitation'),
    url(r'^accept_or_decline_ref_invitations/$',
        views.accept_or_decline_ref_invitations, name='accept_or_decline_ref_invitations'),
    url(r'^accept_or_decline_ref_invitations/(?P<invitation_id>[0-9]+)$',
        views.accept_or_decline_ref_invitations, name='accept_or_decline_ref_invitations'),
    url(r'^decline_ref_invitation/(?P<invitation_key>.+)$',
        views.decline_ref_invitation, name='decline_ref_invitation'),
    url(r'^ref_invitation_reminder/{regex}/(?P<invitation_id>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.ref_invitation_reminder, name='ref_invitation_reminder'),
    url(r'^cancel_ref_invitation/{regex}/(?P<invitation_id>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.cancel_ref_invitation, name='cancel_ref_invitation'),
    url(r'^extend_refereeing_deadline/{regex}/(?P<days>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.extend_refereeing_deadline, name='extend_refereeing_deadline'),
    url(r'^set_refereeing_deadline/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.set_refereeing_deadline, name='set_refereeing_deadline'),
    url(r'^close_refereeing_round/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.close_refereeing_round, name='close_refereeing_round'),
    url(r'^refereeing_overview$', views.refereeing_overview, name='refereeing_overview'),
    url(r'^communication/{regex}/(?P<comtype>[a-zA-Z]{{4,}})$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.communication, name='communication'),
    url(r'^communication/{regex}/(?P<comtype>[a-zA-Z]{{4,}})/(?P<referee_id>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.communication, name='communication'),
    url(r'^eic_recommendation/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.eic_recommendation, name='eic_recommendation'),
    url(r'^eic_recommendation/{regex}/reformulate$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.reformulate_eic_recommendation, name='reformulate_eic_recommendation'),
    url(r'^cycle/{regex}/submit$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.cycle_form_submit, name='cycle_confirmation'),

    # Reports
    url(r'^{regex}/reports/submit$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submit_report, name='submit_report'),
    url(r'^reports/vet$', views.vet_submitted_reports_list, name='vet_submitted_reports_list'),
    url(r'^reports/(?P<report_id>[0-9]+)/vet$', views.vet_submitted_report,
        name='vet_submitted_report'),

    # Voting
    url(r'^prepare_for_voting/(?P<rec_id>[0-9]+)$', views.prepare_for_voting,
        name='prepare_for_voting'),
    url(r'^vote_on_rec/(?P<rec_id>[0-9]+)$', views.vote_on_rec, name='vote_on_rec'),
    url(r'^remind_Fellows_to_vote$', views.remind_Fellows_to_vote,
        name='remind_Fellows_to_vote'),
]
