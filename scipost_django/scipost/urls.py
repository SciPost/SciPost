__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.urls import include, path, re_path

from . import views, sso
from .feeds import (
    LatestNewsFeedRSS,
    LatestNewsFeedAtom,
    LatestCommentsFeedRSS,
    LatestCommentsFeedAtom,
    LatestSubmissionsFeedRSS,
    LatestSubmissionsFeedAtom,
    LatestPublicationsFeedRSS,
    LatestPublicationsFeedAtom,
    DjangoJobOpeningsFeedRSS,
)

from journals import views as journals_views
from journals.regexes import (
    ISSUE_DOI_LABEL_REGEX,
    PUBLICATION_DOI_LABEL_REGEX,
    DOI_DISPATCH_PATTERN,
)
from submissions import views as submission_views


favicon_view = RedirectView.as_view(
    url="/static/scipost/images/scipost_favicon.png", permanent=True
)


app_name = "scipost"


urlpatterns = [
    #
    #######################
    # redirect for favicon
    #######################
    path("favicon\.ico", favicon_view),
    #
    #############
    # Utilities:
    #############
    #
    ###########################
    # Test Sentry installation
    ###########################
    path("sentry-debug/", views.trigger_error, name="trigger_error"),
    #
    ###############
    # Autocomplete
    ###############
    path(
        "contributor-autocomplete",
        views.HXDynselContributorAutocomplete.as_view(),
        name="contributor-autocomplete",
    ),
    path(
        "group-autocomplete",
        views.GroupAutocompleteView.as_view(),
        name="group-autocomplete",
    ),
    path(
        "user-autocomplete",
        views.UserAutocompleteView.as_view(),
        name="user-autocomplete",
    ),
    #
    #########
    # Search
    #########
    path(
        "search",
        TemplateView.as_view(template_name="search/search.html"),
        name="search",
    ),
    #
    ###########
    # Homepage
    ###########
    path("", views.portal, name="index"),
    #
    ####################################
    # HTMX-delivered homepage fragments
    ####################################
    path("portal/_hx_home", views.portal_hx_home, name="portal_hx_home"),
    path("portal/_hx_journals", views.portal_hx_journals, name="portal_hx_journals"),
    path(
        "portal/_hx_publications",
        views.portal_hx_publications,
        name="portal_hx_publications",
    ),
    path(
        "portal/_hx_publications/search_form",
        views.PortalPublicationSearchView.as_view(),
        name="_hx_publication_search_form_view",
    ),
    path(
        "portal/_hx_recent_publications",
        views.portal_hx_recent_publications,
        name="portal_hx_recent_publications",
    ),
    path(
        "portal/_hx_submissions",
        views.portal_hx_submissions,
        name="portal_hx_submissions",
    ),
    path(
        "portal/_hx_submissions_needing_reports",
        views.portal_hx_submissions_needing_reports,
        name="portal_hx_submissions_needing_reports",
    ),
    path(
        "portal/_hx_submissions/search_form",
        views.PortalSubmissionSearchView.as_view(),
        name="_hx_submission_search_form_view",
    ),
    path(
        "portal/_hx_submissions_needing_reports/search_form",
        views.PortalSubmissionNeedingReportsSearchView.as_view(),
        name="_hx_submission_needing_reports_search_form_view",
    ),
    path("portal/_hx_reports", views.portal_hx_reports, name="portal_hx_reports"),
    path(
        "portal/_hx_reports_page",
        views.portal_hx_reports_page,
        name="portal_hx_reports_page",
    ),
    path("portal/_hx_comments", views.portal_hx_comments, name="portal_hx_comments"),
    path(
        "portal/_hx_comments_page",
        views.portal_hx_comments_page,
        name="portal_hx_comments_page",
    ),
    path(
        "portal/_hx_commentaries",
        views.portal_hx_commentaries,
        name="portal_hx_commentaries",
    ),
    path(
        "portal/_hx_commentaries_page",
        views.portal_hx_commentaries_page,
        name="portal_hx_commentaries_page",
    ),
    path("portal/_hx_theses", views.portal_hx_theses, name="portal_hx_theses"),
    path(
        "portal/_hx_theses_page",
        views.portal_hx_theses_page,
        name="portal_hx_theses_page",
    ),
    path("_hx_news", views._hx_news, name="_hx_news"),
    path(
        "_hx_participates_in",
        TemplateView.as_view(template_name="scipost/_hx_participates_in.html"),
        name="_hx_participates_in",
    ),
    path("_hx_sponsors", views._hx_sponsors, name="_hx_sponsors"),
    #
    ####################
    # General use pages
    ####################
    path("files/secure/<path:path>", views.protected_serve, name="secure_file"),
    path(
        "error", TemplateView.as_view(template_name="scipost/error.html"), name="error"
    ),
    path(
        "acknowledgement",
        TemplateView.as_view(template_name="scipost/acknowledgement.html"),
        name="acknowledgement",
    ),
    path("messages", views._hx_messages, name="_hx_messages"),
    #
    #######
    # Info
    #######
    path(
        "about", TemplateView.as_view(template_name="scipost/about.html"), name="about"
    ),
    path(
        "contact",
        TemplateView.as_view(template_name="scipost/contact.html"),
        name="contact",
    ),
    path("call", TemplateView.as_view(template_name="scipost/call.html"), name="call"),
    path(
        "donations/thank-you/",
        TemplateView.as_view(template_name="scipost/donation_thank_you.html"),
        name="donation_thank_you",
    ),
    path(
        "ExpSustDrive2018",
        TemplateView.as_view(template_name="scipost/ExpSustDrive2018.html"),
        name="ExpSustDrive2018",
    ),
    path(
        "PlanSciPost",
        TemplateView.as_view(template_name="scipost/PlanSciPost.html"),
        name="PlanSciPost",
    ),
    path(
        "roadmap",
        TemplateView.as_view(template_name="scipost/roadmap.html"),
        name="roadmap",
    ),
    path(
        "foundation",
        TemplateView.as_view(template_name="scipost/foundation.html"),
        name="foundation",
    ),
    path(
        "tour",
        TemplateView.as_view(template_name="scipost/quick_tour.html"),
        name="quick_tour",
    ),
    path("FAQ", TemplateView.as_view(template_name="scipost/FAQ.html"), name="FAQ"),
    path(
        "terms_and_conditions",
        TemplateView.as_view(template_name="scipost/terms_and_conditions.html"),
        name="terms_and_conditions",
    ),
    path(
        "privacy_policy",
        TemplateView.as_view(template_name="scipost/privacy_policy.html"),
        name="privacy_policy",
    ),
    path(
        "posi",
        TemplateView.as_view(template_name="scipost/posi.html"),
        name="posi",
    ),
    #
    ########
    # Feeds
    ########
    path("feeds", views.feeds, name="feeds"),
    path("rss/news/", LatestNewsFeedRSS(), name="feeds_rss_news"),
    path("atom/news/", LatestNewsFeedAtom(), name="feeds_atom_news"),
    path("rss/comments/", LatestCommentsFeedRSS(), name="feeds_rss_comments"),
    path("atom/comments/", LatestCommentsFeedAtom(), name="feeds_atom_comments"),
    path("rss/submissions/", LatestSubmissionsFeedRSS(), name="feeds_rss_submissions"),
    path(
        "rss/submissions/<specialty:specialty>",
        LatestSubmissionsFeedRSS(),
        name="sub_feed_spec_rss",
    ),
    path(
        "atom/submissions/", LatestSubmissionsFeedAtom(), name="feeds_atom_submissions"
    ),
    path(
        "atom/submissions/<specialty:specialty>",
        LatestSubmissionsFeedAtom(),
        name="sub_feed_spec_atom",
    ),
    path(
        "rss/publications/", LatestPublicationsFeedRSS(), name="feeds_rss_publications"
    ),
    path(
        "rss/publications/<specialty:specialty>",
        LatestPublicationsFeedRSS(),
        name="pub_feed_spec_rss",
    ),
    path(
        "atom/publications/",
        LatestPublicationsFeedAtom(),
        name="feeds_atom_publications",
    ),
    path(
        "rss/careers/django/",
        DjangoJobOpeningsFeedRSS(),
        name="feeds_django_job_openings",
    ),
    path(
        "atom/publications/<specialty:specialty>",
        LatestPublicationsFeedAtom(),
        name="pub_feed_spec_atom",
    ),
    #
    ################
    # Contributors:
    ################
    #
    #################################
    # Contributor info (public view)
    #################################
    path(
        "contributor/<int:contributor_id>",
        views.contributor_info,
        name="contributor_info",
    ),
    #
    ###############
    # Registration
    ###############
    path("register", views.register, name="register"),
    path(
        "thanks_for_registering",
        TemplateView.as_view(template_name="scipost/thanks_for_registering.html"),
        name="thanks_for_registering",
    ),
    path(
        "activation/<int:contributor_id>/<str:key>/",
        views.activation,
        name="activation",
    ),
    path(
        "activation/<int:contributor_id>/<str:key>/renew",
        views.request_new_activation_link,
        name="request_new_activation_link",
    ),
    path(
        "unsubscribe/<int:contributor_id>/<str:key>",
        views.unsubscribe,
        name="unsubscribe",
    ),
    path(
        "vet_registration_requests",
        views.vet_registration_requests,
        name="vet_registration_requests",
    ),
    path(
        "_hx_vet_registration_request_ack_form/<int:contributor_id>",
        views._hx_vet_registration_request_ack_form,  # type: ignore
        name="_hx_vet_registration_request_ack_form",
    ),
    path(
        "registration_requests",
        views.registration_requests,
        name="registration_requests",
    ),
    path(
        "registration_requests/<int:contributor_id>/reset",
        views.registration_requests_reset,
        name="registration_requests_reset",
    ),
    #
    #################################################################
    # Registration invitations (Never change this route! Thank you.)
    #################################################################
    path("invitation/<str:key>", views.invitation, name="invitation"),
    #
    #################
    # Authentication
    #################
    path("login/", views.SciPostLoginView.as_view(), name="login"),
    path("logout/", views.SciPostLogoutView.as_view(), name="logout"),
    path(
        "password_change",
        views.SciPostPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password_reset/",
        views.SciPostPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "reset/<uidb64>/<token>",
        views.SciPostPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "update_personal_data", views.update_personal_data, name="update_personal_data"
    ),
    path(
        "_hx_accepts_scipost_emails_checkbox",
        views._hx_accepts_scipost_emails_checkbox,
        name="_hx_accepts_scipost_emails_checkbox",
    ),
    path(
        "_hx_accepts_refereeing_requests_checkbox",
        views._hx_accepts_refereeing_requests_checkbox,
        name="_hx_accepts_refereeing_requests_checkbox",
    ),
    path("totp/", views.TOTPListView.as_view(), name="totp"),
    path("totp/create", views.TOTPDeviceCreateView.as_view(), name="totp_create"),
    path(
        "totp/<int:device_id>/delete",
        views.TOTPDeviceDeleteView.as_view(),
        name="totp_delete",
    ),
    #
    ############################################
    # Single sign-on [for GitLab: see api/urls]
    ############################################
    path("sso_discourse", sso.discourse, name="sso_discourse"),
    #
    ################
    # Personal Page
    ################
    path("personal_page/", views.personal_page, name="personal_page"),
    path(
        "personal_page/update_orcid_from_authentication",
        views.update_orcid_from_authentication,
        name="update_orcid_from_authentication",
    ),
    path(
        "personal_page/_hx_account",
        views.personal_page_hx_account,
        name="personal_page_hx_account",
    ),
    path(
        "personal_page/_hx_admin",
        views.personal_page_hx_admin,
        name="personal_page_hx_admin",
    ),
    path(
        "personal_page/_hx_edadmin",
        views.personal_page_hx_edadmin,
        name="personal_page_hx_edadmin",
    ),
    path(
        "personal_page/_hx_refereeing",
        views.personal_page_hx_refereeing,
        name="personal_page_hx_refereeing",
    ),
    path(
        "personal_page/_hx_publications",
        views.personal_page_hx_publications,
        name="personal_page_hx_publications",
    ),
    path(
        "personal_page/_hx_email_preferences",
        views.personal_page_hx_email_preferences,
        name="personal_page_hx_email_preferences",
    ),
    path(
        "personal_page/_hx_submissions",
        views.personal_page_hx_submissions,
        name="personal_page_hx_submissions",
    ),
    path(
        "personal_page/_hx_commentaries",
        views.personal_page_hx_commentaries,
        name="personal_page_hx_commentaries",
    ),
    path(
        "personal_page/_hx_theses",
        views.personal_page_hx_theses,
        name="personal_page_hx_theses",
    ),
    path(
        "personal_page/_hx_comments",
        views.personal_page_hx_comments,
        name="personal_page_hx_comments",
    ),
    path(
        "personal_page/_hx_author_replies",
        views.personal_page_hx_author_replies,
        name="personal_page_hx_author_replies",
    ),
    #
    ###################
    # Unavailabilities
    ###################
    path(
        "_hx_unavailability/",
        include(
            [
                path(
                    "",
                    views._hx_unavailability,
                    name="_hx_unavailability",
                ),
                path(
                    "<int:pk>",
                    views._hx_unavailability,
                    name="_hx_unavailability",
                ),
            ]
        ),
    ),
    #
    ####################
    # Authorship claims
    ####################
    path("claim_authorships", views.claim_authorships, name="claim_authorships"),
    path(
        "claim_sub_authorship/<int:submission_id>/<int:claim>",
        views.claim_sub_authorship,
        name="claim_sub_authorship",
    ),
    path(
        "claim_com_authorship/<int:commentary_id>/<int:claim>",
        views.claim_com_authorship,
        name="claim_com_authorship",
    ),
    path(
        "claim_thesis_authorship/<int:thesis_id>/<int:claim>",
        views.claim_thesis_authorship,
        name="claim_thesis_authorship",
    ),
    path(
        "vet_authorship_claims",
        views.vet_authorship_claims,
        name="vet_authorship_claims",
    ),
    path(
        "vet_authorship_claim/<int:claim_id>/<int:claim>",
        views.vet_authorship_claim,
        name="vet_authorship_claim",
    ),
    #
    ###################
    # Email facilities
    ###################
    path("email_group_members", views.email_group_members, name="email_group_members"),
    path("email_particular", views.email_particular, name="email_particular"),
    path(
        "send_precooked_email", views.send_precooked_email, name="send_precooked_email"
    ),
    #
    ####################
    # Editorial College
    ####################
    path(
        "EdCol_by-laws",
        TemplateView.as_view(template_name="scipost/EdCol_by-laws.html"),
        name="EdCol_by-laws",
    ),
    path(
        "EdCol_by-laws_Changes_2023_02",
        TemplateView.as_view(
            template_name="scipost/EdCol_by-laws_Changes_2023-02.html"
        ),
        name="EdCol_by-laws_Changes_2023_02",
    ),
    path(
        "EdCol_by-laws_Changes_2022_11",
        TemplateView.as_view(
            template_name="scipost/EdCol_by-laws_Changes_2022-11.html"
        ),
        name="EdCol_by-laws_Changes_2022_11",
    ),
    path(
        "EdCol_by-laws_Changes_2021_04",
        TemplateView.as_view(
            template_name="scipost/EdCol_by-laws_Changes_2021-04.html"
        ),
        name="EdCol_by-laws_Changes_2021_04",
    ),
    #
    ###############
    # Publications
    ###############
    #
    ##########
    # Reports
    ##########
    path(
        "<report_doi_label:doi_label>",
        journals_views.report_detail,
        name="report_detail",
    ),
    #
    ###########
    # Comments
    ###########
    path(
        "<comment_doi_label:doi_label>",
        journals_views.comment_detail,
        name="comment_detail",
    ),
    #
    #################
    # Author Replies
    #################
    path(
        "<author_reply_doi_label:doi_label>",
        journals_views.author_reply_detail,
        name="author_reply_detail",
    ),
    #
    ############################
    # Publication detail (+pdf)
    ############################
    re_path(
        "^10.21468/{pattern}$".format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch,
        name="doi_dispatch",
    ),
    re_path(
        "^{pattern}$".format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch,
        name="doi_dispatch",
    ),
    path(
        "10.21468/<publication_doi_label:doi_label>",
        journals_views.publication_detail,
        name="publication_detail",
    ),
    path(
        "<publication_doi_label:doi_label>",
        journals_views.publication_detail,
        name="publication_detail",
    ),
    path(
        "10.21468/<publication_doi_label:doi_label>/pdf",
        journals_views.publication_detail_pdf,
        name="publication_pdf",
    ),
    path(
        "<publication_doi_label:doi_label>/pdf",
        journals_views.publication_detail_pdf,
        name="publication_pdf",
    ),
    #
    ######################
    # Publication updates
    ######################
    path(
        "<publication_doi_label:doi_label>-update-<int:update_nr>",
        journals_views.publication_update_detail,
        name="publication_update_detail",
    ),
    path(
        "10.21468/<publication_doi_label:doi_label>-update-<int:update_nr>",
        journals_views.publication_update_detail,
        name="publication_update_detail",
    ),
    #
    ################
    # Journal issue
    ################
    path(
        "10.21468/<issue_doi_label:doi_label>",
        journals_views.issue_detail,
        name="issue_detail",
    ),
    path(
        "<issue_doi_label:doi_label>", journals_views.issue_detail, name="issue_detail"
    ),
    #
    #######################
    # Journal landing page
    #######################
    path(
        "10.21468/<journal_doi_label:doi_label>",
        journals_views.journal_detail,
        name="journal_detail",
    ),
    path(
        "<journal_doi_label:doi_label>",
        journals_views.journal_detail,
        name="journal_detail",
    ),
    path(
        "arxiv_doi_feed/<journal_doi_label:doi_label>",
        journals_views.arxiv_doi_feed,
        name="arxiv_doi_feed",
    ),
    path(
        "arxiv_doi_feed",
        journals_views.arxiv_doi_feed,
        name="arxiv_doi_feed",
    ),
    #
    ###############
    # Howto guides
    ###############
    path(
        "howto", TemplateView.as_view(template_name="scipost/howto.html"), name="howto"
    ),
    path(
        "howto/production",
        TemplateView.as_view(template_name="scipost/howto_production.html"),
        name="howto_production",
    ),
    #
    ######################
    # Pwning verification
    ######################
    path(
        "have-i-been-pwned-verification.txt",
        views.have_i_been_pwned,
        name="have_i_been_pwned",
    ),
]
