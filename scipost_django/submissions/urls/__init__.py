__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, re_path, register_converter
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from journals.converters import JournalDOILabelConverter

from ontology.converters import AcademicFieldSlugConverter

from ..converters import (
    IdentifierConverter,
    IdentifierWithoutVersionNumberConverter,
    ReportDOILabelConverter,
)

from .. import views

app_name = "submissions"

# converters
register_converter(JournalDOILabelConverter, "journal_doi_label")
register_converter(AcademicFieldSlugConverter, "acad_field")
register_converter(IdentifierWithoutVersionNumberConverter, "identifier_wo_vn_nr")
register_converter(IdentifierConverter, "identifier")
register_converter(ReportDOILabelConverter, "report_doi_label")


urlpatterns = [
    # nested namespaces
    path("pool/", include("submissions.urls.pool", namespace="pool")),
    # Autocomplete
    path(
        "submission-autocomplete",
        views.SubmissionAutocompleteView.as_view(),
        name="submission-autocomplete",
    ),
    # Information
    path(
        "author_guidelines",
        TemplateView.as_view(template_name="submissions/author_guidelines.html"),
        name="author_guidelines",
    ),
    path(
        "editorial_procedure",
        TemplateView.as_view(template_name="submissions/editorial_procedure.html"),
        name="editorial_procedure",
    ),
    path(  # deprecated 2022-11-23, replaced by editorial_procedure; keep active for now
        "refereeing_procedure",
        RedirectView.as_view(
            pattern_name="submissions:editorial_procedure", permanent=True
        ),
        name="refereeing_procedure",
    ),
    path(
        "referee_guidelines",
        TemplateView.as_view(template_name="submissions/referee_guidelines.html"),
        name="referee_guidelines",
    ),
    # Submissions
    path("", views.SubmissionListView.as_view(), name="submissions"),
    path(
        "<identifier_wo_vn_nr:identifier_wo_vn_nr>/",
        views.submission_detail_wo_vn_nr,
        name="submission_wo_vn_nr",
    ),
    path(
        "referee_indications/<int:pk>/delete",
        views._hx_referee_indication_delete,
        name="_hx_referee_indication_delete",
    ),
    path(
        "referee_indications/<int:pk>/delete/<str:invitation_key>",
        views._hx_referee_indication_delete,
        name="_hx_referee_indication_delete",
    ),
    # path(
    #     "referee_indications/<int:pk>/edit",
    #     views._hx_referee_indication_edit,
    #     name="_hx_referee_indication_edit",
    # ),
    path(
        "<identifier:identifier_w_vn_nr>/",
        include(
            [
                path(
                    "",
                    views.submission_detail,
                    name="submission",
                ),
                path(
                    "reset_refereeing_cycle",
                    views.reset_refereeing_cycle,
                    name="reset_refereeing_cycle",
                ),
                path(
                    "referee_indications/",
                    include(
                        [
                            path(
                                "",
                                views.referee_indications,
                                name="referee_indications",
                            ),
                            path(
                                "table",
                                views._hx_referee_indication_table,
                                name="_hx_referee_indication_table",
                            ),
                            path(
                                "_hx_formset",
                                views.HXRefereeIndicationFormSetView.as_view(),
                                name="_hx_referee_indication_formset",
                            ),
                        ]
                    ),
                ),
                # Topics
                path(
                    "_hx_submission_topics/",
                    include(
                        [
                            path(
                                "",
                                views._hx_submission_topics,
                                name="_hx_submission_topics",
                            ),
                            path(
                                "<slug:topic_slug>/action/<str:action>",
                                views._hx_submission_topic_action,
                                name="_hx_submission_topic_action",
                            ),
                        ]
                    ),
                ),
                # Fellowship
                path(
                    "_hx_submission_autoupdate_fellowship",
                    views._hx_submission_autoupdate_fellowship,
                    name="_hx_submission_autoupdate_fellowship",
                ),
            ]
        ),
    ),
    path(
        "workflow_diagram",
        views._hx_submission_workflow_diagram,
        name="_hx_submission_workflow_diagram",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/workflow_diagram",
        views._hx_submission_workflow_diagram,
        name="_hx_submission_workflow_diagram",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/reports/<int:report_nr>/pdf",
        views.report_detail_pdf,
        name="report_detail_pdf",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/reports/<int:report_nr>/attachment",
        views.report_attachment,
        name="report_attachment",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/reports/pdf",
        views.submission_refereeing_package_pdf,
        name="refereeing_package_pdf",
    ),
    # Editorial Administration
    path(
        "admin/treated", views.treated_submissions_list, name="treated_submissions_list"
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_target_journal",
        views._hx_submission_update_target_journal,
        name="_hx_submission_update_target_journal",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_target_journal_form",
        views._hx_submission_update_target_journal_form,
        name="_hx_submission_update_target_journal_form",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_target_proceedings",
        views._hx_submission_update_target_proceedings,
        name="_hx_submission_update_target_proceedings",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_target_proceedings_form",
        views._hx_submission_update_target_proceedings_form,
        name="_hx_submission_update_target_proceedings_form",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_collections",
        views._hx_submission_update_collections,
        name="_hx_submission_update_collections",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_collections_form",
        views._hx_submission_update_collections_form,
        name="_hx_submission_update_collections_form",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_preprint_file",
        views._hx_submission_update_preprint_file,
        name="_hx_submission_update_preprint_file",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_update_preprint_file_form",
        views._hx_submission_update_preprint_file_form,
        name="_hx_submission_update_preprint_file_form",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/_hx_submission_add_specialty",
        views._hx_submission_add_specialty,
        name="_hx_submission_add_specialty",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/preassignment",
        views.PreassignmentView.as_view(),
        name="do_preassignment",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/conflicts",
        views.SubmissionConflictsView.as_view(),
        name="conflicts",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editor_invitations",
        views.editor_invitations,
        name="editor_invitations",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editor_invitations/<int:assignment_id>",
        views.send_editorial_assignment_invitation,
        name="send_editorial_assignment_invitation",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/reassign_editor",
        views.SubmissionReassignmentView.as_view(),
        name="reassign_submission",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/reports/compile",
        views.treated_submission_pdf_compile,
        name="treated_submission_pdf_compile",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/plagiarism",
        views.PlagiarismView.as_view(),
        name="plagiarism",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/plagiarism/iThenticate_report",
        views.PlagiarismReportPDFView.as_view(),
        name="iThenticate_plagiarism_report",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/plagiarism/internal",
        views.PlagiarismInternalView.as_view(),
        name="plagiarism_internal",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/recommendation",
        views.EICRecommendationDetailView.as_view(),
        name="eic_recommendation_detail",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editorial_decision/create",
        views.EditorialDecisionCreateView.as_view(),
        name="editorial_decision_create",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editorial_decision",
        views.EditorialDecisionDetailView.as_view(),
        name="editorial_decision_detail",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editorial_decision/update",
        views.EditorialDecisionUpdateView.as_view(),
        name="editorial_decision_update",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/editorial_decision/fix",
        views.fix_editorial_decision,
        name="fix_editorial_decision",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/accept_puboffer",
        views.accept_puboffer,
        name="accept_puboffer",
    ),
    path(
        "admin/<identifier:identifier_w_vn_nr>/restart_refereeing",
        views.restart_refereeing,
        name="restart_refereeing",
    ),
    path("admin/reports", views.reports_accepted_list, name="reports_accepted_list"),
    path(
        "admin/reports/<int:report_id>/compile",
        views.report_pdf_compile,
        name="report_pdf_compile",
    ),
    path(
        "admin/reports/<int:report_id>/_hx_anonymize_report",
        views._hx_anonymize_report,
        name="_hx_anonymize_report",
    ),
    # Submission, resubmission, withdrawal
    path(  # Start a new submission process; choose resub or new sub (with field choice)
        "submit_manuscript", views.submit_manuscript, name="submit_manuscript"
    ),
    path(  # Choose journal (thread_hash as GET param if resubmission)
        "submit/<acad_field:acad_field>",
        views.submit_choose_journal,
        name="submit_choose_journal",
    ),
    path(  # Choose preprint server (thread_hash as GET param if resubmission)
        "submit/<journal_doi_label:journal_doi_label>",
        views.submit_choose_preprint_server,
        name="submit_choose_preprint_server",
    ),
    path(  # Submit using the SciPost preprint server (thread_hash as GET param if resubmission)
        "submit_manuscript/<journal_doi_label:journal_doi_label>/scipost",
        views.RequestSubmissionUsingSciPostView.as_view(),
        name="submit_manuscript_scipost",
    ),
    path(  # Submit using arXiv (thread_hash as GET param if resubmission)
        "submit_manuscript/<journal_doi_label:journal_doi_label>/arxiv",
        views.RequestSubmissionUsingArXivView.as_view(),
        name="submit_manuscript_arxiv",
    ),
    path(  # Submit using ChemRxiv (thread_hash as GET param if resubmission)
        "submit_manuscript/<journal_doi_label:journal_doi_label>/chemrxiv",
        views.RequestSubmissionUsingChemRxivView.as_view(),
        name="submit_manuscript_chemrxiv",
    ),
    path(  # Submit using a Figshare-related preprint server (thread_hash as GET param if resubmission)
        "submit_manuscript/<journal_doi_label:journal_doi_label>/figshare",
        views.RequestSubmissionUsingFigshareView.as_view(),
        name="submit_manuscript_figshare",
    ),
    path(  # Submit using a OSFPreprints-related preprint server (thread_hash as GET param if resubmission)
        "submit_manuscript/<journal_doi_label:journal_doi_label>/osfpreprints",
        views.RequestSubmissionUsingOSFPreprintsView.as_view(),
        name="submit_manuscript_osfpreprints",
    ),
    path(
        "submit_manuscript/<identifier:identifier_w_vn_nr>/indicate_referees",
        views.submit_indicate_referees,
        name="submit_indicate_referees",
    ),
    path(
        "withdraw_manuscript/<identifier:identifier_w_vn_nr>/",
        views.withdraw_manuscript,
        name="withdraw_manuscript",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/extend_assignment_deadline/<int:days>",
        views.extend_assignment_deadline,
        name="extend_assignment_deadline",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/extend_assignment_deadline",
        views.extend_assignment_deadline,
        name="extend_assignment_deadline",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/conditional_assignment_offer/<int:offer_id>/accept",
        views.accept_conditional_assignment_offer,
        name="accept_conditional_assignment_offer",
    ),
    path(
        "assignment_failed/<identifier:identifier_w_vn_nr>",
        views.assignment_failed,
        name="assignment_failed",
    ),
    # Editorial workflow and refereeing
    path("editorial_workflow", views.editorial_workflow, name="editorial_workflow"),
    path("assignments", views.assignments, name="assignments"),
    path(
        "editorial_page/<identifier:identifier_w_vn_nr>",
        views.editorial_page,
        name="editorial_page",
    ),
    path(
        "select_referee/<identifier:identifier_w_vn_nr>",
        views.select_referee,
        name="select_referee",
    ),
    path(
        "_hx_select_referee_table/<identifier:identifier_w_vn_nr>",
        views._hx_select_referee_table,
        name="_hx_select_referee_table",
    ),
    path(
        "_hx_select_referee_search_form/<identifier:identifier_w_vn_nr>/<str:filter_set>",
        views._hx_select_referee_search_form,
        name="_hx_select_referee_search_form",
    ),
    path(
        "add_referee_profile/<identifier:identifier_w_vn_nr>",
        views.add_referee_profile,
        name="add_referee_profile",
    ),
    path(
        "invite_referee/<identifier:identifier_w_vn_nr>/<int:profile_id>/custom/<str:profile_email>/auto_remind_<str:auto_reminders_allowed>",
        views.invite_referee,
        name="invite_referee",
    ),
    path(
        "invite_referee/<identifier:identifier_w_vn_nr>/<int:profile_id>/quick",
        views._hx_quick_invite_referee,
        name="_hx_quick_invite_referee",
    ),
    path(
        "refereeing/_hx_customize_invitation/<identifier:identifier_w_vn_nr>/<int:profile_id>",
        views._hx_customize_refereeing_invitation,
        name="_hx_customize_refereeing_invitation",
    ),
    path(
        "refereeing/_hx_add_referee_profile_email/<int:profile_id>",
        views._hx_add_referee_profile_email,
        name="_hx_add_referee_profile_email",
    ),
    path(
        "set_refinv_auto_reminder/<int:invitation_id>/<int:auto_reminders>",
        views.set_refinv_auto_reminder,
        name="set_refinv_auto_reminder",
    ),
    path(
        "accept_or_decline_ref_invitations/",
        views.accept_or_decline_ref_invitations,
        name="accept_or_decline_ref_invitations",
    ),
    path(
        "accept_or_decline_ref_invitations/<int:invitation_id>",
        views.accept_or_decline_ref_invitations,
        name="accept_or_decline_ref_invitations",
    ),
    path(
        "decline_ref_invitation/<str:invitation_key>",
        views.decline_ref_invitation,
        name="decline_ref_invitation",
    ),
    path(
        "ref_invitation_reminder/<identifier:identifier_w_vn_nr>/<int:invitation_id>",
        views.ref_invitation_reminder,
        name="ref_invitation_reminder",
    ),
    path(
        "_hx_cancel_ref_invitation/<identifier:identifier_w_vn_nr>/<int:invitation_id>",
        views._hx_cancel_ref_invitation,
        name="_hx_cancel_ref_invitation",
    ),
    path(
        "_hx_report_intended_delivery_form/<int:invitation_id>",
        views._hx_report_intended_delivery_form,
        name="_hx_report_intended_delivery_form",
    ),
    path(
        "extend_refereeing_deadline/<identifier:identifier_w_vn_nr>/<int:days>",
        views.extend_refereeing_deadline,
        name="extend_refereeing_deadline",
    ),
    path(
        "set_refereeing_deadline/<identifier:identifier_w_vn_nr>",
        views.set_refereeing_deadline,
        name="set_refereeing_deadline",
    ),
    path(
        "close_refereeing_round/<identifier:identifier_w_vn_nr>",
        views.close_refereeing_round,
        name="close_refereeing_round",
    ),
    path("refereeing_overview", views.refereeing_overview, name="refereeing_overview"),
    path(
        "communication/<identifier:identifier_w_vn_nr>/<str:comtype>/<int:referee_id>",
        views.communication,
        name="communication",
    ),
    path(
        "communication/<identifier:identifier_w_vn_nr>/<str:comtype>",
        views.communication,
        name="communication",
    ),
    path(
        "eic_recommendation/<identifier:identifier_w_vn_nr>/_hx_form",
        views._hx_eic_recommendation_form,
        name="_hx_eic_recommendation_form",
    ),
    path(
        "eic_recommendation/<identifier:identifier_w_vn_nr>",
        views.eic_recommendation,
        name="eic_recommendation",
    ),
    path(
        "eic_recommendation/<identifier:identifier_w_vn_nr>/reformulate",
        views.reformulate_eic_recommendation,
        name="reformulate_eic_recommendation",
    ),
    path(
        "cycle/<identifier:identifier_w_vn_nr>/submit",
        views.cycle_form_submit,
        name="cycle_confirmation",
    ),
    # Reports
    path(
        "<identifier:identifier_w_vn_nr>/reports/submit",
        views.submit_report,
        name="submit_report",
    ),
    path(
        "reports/vet",
        views.vet_submitted_reports_list,
        name="vet_submitted_reports_list",
    ),
    path(
        "reports/<int:report_id>/vet",
        views.vet_submitted_report,
        name="vet_submitted_report",
    ),
    # Voting
    path(
        "prepare_for_voting/<int:rec_id>",
        views.prepare_for_voting,
        name="prepare_for_voting",
    ),
    path("vote_on_rec/<int:rec_id>", views.vote_on_rec, name="vote_on_rec"),
    path(
        "_hx_recommendation_vote_form/<int:rec_id>",
        views._hx_recommendation_vote_form,
        name="_hx_recommendation_vote_form",
    ),
    path(
        "claim_voting_right/<int:rec_id>",
        views.claim_voting_right,
        name="claim_voting_right",
    ),
    path(
        "remind_Fellows_to_vote/<int:rec_id>",
        views.remind_Fellows_to_vote,
        name="remind_Fellows_to_vote",
    ),
    # Monitoring
    path("monitor", views.monitor, name="monitor"),
]
