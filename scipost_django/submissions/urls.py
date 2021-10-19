__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views
from .constants import SUBMISSIONS_WO_VN_REGEX, SUBMISSIONS_COMPLETE_REGEX

app_name = 'submissions'


urlpatterns = [
    # Autocomplete
    path(
        'submission-autocomplete',
        views.SubmissionAutocompleteView.as_view(),
        name='submission-autocomplete'
    ),
    # Submissions
    url(r'^$', views.SubmissionListView.as_view(), name='submissions'),
    url(r'^author_guidelines$',
        TemplateView.as_view(template_name='submissions/author_guidelines.html'),
        name='author_guidelines'),
    url(r'^refereeing_procedure$',
        TemplateView.as_view(template_name='submissions/refereeing_procedure.html'),
        name='refereeing_procedure'),
    url(r'^referee_guidelines$',
        TemplateView.as_view(template_name='submissions/referee_guidelines.html'),
        name='referee_guidelines'),
    url(r'^{regex}/$'.format(regex=SUBMISSIONS_WO_VN_REGEX), views.submission_detail_wo_vn_nr,
        name='submission_wo_vn_nr'),
    url(r'^{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_detail, name='submission'),
    url(r'^{regex}/reports/(?P<report_nr>[0-9]+)/pdf$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.report_detail_pdf, name='report_detail_pdf'),
    url(r'^{regex}/reports/(?P<report_nr>[0-9]+)/attachment$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.report_attachment, name='report_attachment'),
    url(r'^{regex}/reports/pdf$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_refereeing_package_pdf, name='refereeing_package_pdf'),

    # Topics
    url(r'^submission_add_topic/{regex}/'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_add_topic,
        name='submission_add_topic'),
    url(r'^submission_remove_topic/{regex}/(?P<slug>[-\w]+)/'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.submission_remove_topic,
        name='submission_remove_topic'),

    # Editorial Administration
    url(r'^admin/treated$', views.treated_submissions_list, name='treated_submissions_list'),
    url(r'^admin/{regex}/prescreening$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PreScreeningView.as_view(), name='do_prescreening'),
    url(r'^admin/{regex}/conflicts$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.SubmissionConflictsView.as_view(), name='conflicts'),
    url(r'^admin/{regex}/editor_invitations$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.editor_invitations, name='editor_invitations'),
    url(r'^admin/{regex}/editor_invitations/(?P<assignment_id>[0-9]+)$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.send_editorial_assignment_invitation,
        name='send_editorial_assignment_invitation'),
    url(r'^admin/{regex}/reassign_editor$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.SubmissionReassignmentView.as_view(),
        name='reassign_submission'),
    url(r'^admin/{regex}/reports/compile$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.treated_submission_pdf_compile, name='treated_submission_pdf_compile'),
    url(r'^admin/{regex}/plagiarism$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PlagiarismView.as_view(), name='plagiarism'),
    url(r'^admin/{regex}/plagiarism/report$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PlagiarismReportPDFView.as_view(), name='plagiarism_report'),
url(r'^admin/{regex}/plagiarism/internal$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.PlagiarismInternalView.as_view(), name='plagiarism_internal'),
    url(
        r'^admin/{regex}/recommendation$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.EICRecommendationDetailView.as_view(),
        name='eic_recommendation_detail'
    ),
    url(
        r'^admin/{regex}/editorial_decision/create$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.EditorialDecisionCreateView.as_view(),
        name='editorial_decision_create'
        ),
    url(
        r'^admin/{regex}/editorial_decision$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.EditorialDecisionDetailView.as_view(),
        name='editorial_decision_detail'
        ),
    url(
        r'^admin/{regex}/editorial_decision/update$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.EditorialDecisionUpdateView.as_view(),
        name='editorial_decision_update'
        ),
    url(
        r'^admin/{regex}/editorial_decision/fix$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.fix_editorial_decision,
        name='fix_editorial_decision'
        ),
    url(
        r'^{regex}/accept_puboffer$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.accept_puboffer,
        name='accept_puboffer'
        ),
    url(
        r'admin/{regex}/restart_refereeing$'.format(
            regex=SUBMISSIONS_COMPLETE_REGEX),
        views.restart_refereeing,
        name='restart_refereeing'
    ),


    url(r'^admin/reports$', views.reports_accepted_list, name='reports_accepted_list'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),
    url(r'^admin/reports/(?P<report_id>[0-9]+)/compile$',
        views.report_pdf_compile, name='report_pdf_compile'),


    # Submission, resubmission, withdrawal

    path( # Start a new submission process; choose resub or new sub (with field choice)
        'submit_manuscript',
        views.submit_manuscript,
        name='submit_manuscript'
    ),
    path( # Choose journal (thread_hash as GET param if resubmission)
        'submit/<acad_field:acad_field>',
        views.submit_choose_journal,
        name='submit_choose_journal'
    ),
    path( # Choose preprint server (thread_hash as GET param if resubmission)
        'submit/<journal_doi_label:journal_doi_label>',
        views.submit_choose_preprint_server,
        name='submit_choose_preprint_server'
    ),

    path( # Submit using the SciPost preprint server (thread_hash as GET param if resubmission)
        'submit_manuscript/<journal_doi_label:journal_doi_label>/scipost',
        views.RequestSubmissionUsingSciPostView.as_view(),
        name='submit_manuscript_scipost'
    ),
    path( # Submit using arXiv (thread_hash as GET param if resubmission)
        'submit_manuscript/<journal_doi_label:journal_doi_label>/arxiv',
        views.RequestSubmissionUsingArXivView.as_view(),
        name='submit_manuscript_arxiv'
    ),
    path( # Submit using ChemRxiv (thread_hash as GET param if resubmission)
        'submit_manuscript/<journal_doi_label:journal_doi_label>/chemrxiv',
        views.RequestSubmissionUsingChemRxivView.as_view(),
        name='submit_manuscript_chemrxiv'
    ),
    path( # Submit using a Figshare-related preprint server (thread_hash as GET param if resubmission)
        'submit_manuscript/<journal_doi_label:journal_doi_label>/figshare',
        views.RequestSubmissionUsingFigshareView.as_view(),
        name='submit_manuscript_figshare'
    ),
    path( # Submit using a OSFPreprints-related preprint server (thread_hash as GET param if resubmission)
        'submit_manuscript/<journal_doi_label:journal_doi_label>/osfpreprints',
        views.RequestSubmissionUsingOSFPreprintsView.as_view(),
        name='submit_manuscript_osfpreprints'
    ),

    url(
        r'^withdraw_manuscript/{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.withdraw_manuscript,
        name='withdraw_manuscript'
    ),

    # Pool
    path(
        'pool2',
        views.pool2,
        name='pool2'
    ),
    path(
        'pool/submissions',
        views.pool_hx_submissions_list,
        name='pool_hx_submissions_list'
    ),
    re_path(
        'pool/submissions/{regex}'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.pool_hx_submission_details,
        name='pool_hx_submission_details'
    ),
    url(r'^pool/$', views.pool, name='pool'),
    url(r'^pool/{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX), views.pool, name='pool'),
    url(r'^add_remark/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.add_remark, name='add_remark'),

    # Assignment of Editor-in-charge
    url(r'^pool/assignment_request/(?P<assignment_id>[0-9]+)$',
        views.assignment_request, name='assignment_request'),
    url(r'^pool/{regex}/editorial_assignment/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.editorial_assignment,
        name='editorial_assignment'),
    url(r'^pool/{regex}/editorial_assignment/(?P<assignment_id>[0-9]+)/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.editorial_assignment,
        name='editorial_assignment'),
    url(r'^update_authors_screening/{regex}/(?P<nrweeks>[1-2])$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.update_authors_screening, name='update_authors_screening'),
    url(r'^assignment_failed/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.assignment_failed, name='assignment_failed'),

    # Editorial workflow and refereeing
    url(r'^editorial_workflow$', views.editorial_workflow, name='editorial_workflow'),
    url(r'^assignments$', views.assignments, name='assignments'),
    url(r'^editorial_page/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.editorial_page, name='editorial_page'),
    url(r'^select_referee/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.select_referee, name='select_referee'),
    url(r'^add_referee_profile/{regex}$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.add_referee_profile, name='add_referee_profile'),
    url(r'^invite_referee/{regex}/(?P<profile_id>[0-9]+)'
        '/(?P<auto_reminders_allowed>[0-1])$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX),
        views.invite_referee, name='invite_referee'),
    url(r'^set_refinv_auto_reminder/(?P<invitation_id>[0-9]+)/(?P<auto_reminders>[0-1])$',
        views.set_refinv_auto_reminder, name='set_refinv_auto_reminder'),
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
    path(
        'claim_voting_right/<int:rec_id>',
        views.claim_voting_right,
        name='claim_voting_right'
    ),
    url(r'^remind_Fellows_to_vote/(?P<rec_id>[0-9]+)$', views.remind_Fellows_to_vote,
        name='remind_Fellows_to_vote'),

    # Monitoring
    path(
        'monitor',
        views.monitor,
        name='monitor'
    ),
]
