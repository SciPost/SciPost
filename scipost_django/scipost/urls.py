__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.urls import include, path, re_path

from . import views, sso
from .feeds import LatestNewsFeedRSS, LatestNewsFeedAtom, LatestCommentsFeedRSS,\
                   LatestCommentsFeedAtom, LatestSubmissionsFeedRSS, LatestSubmissionsFeedAtom,\
                   LatestPublicationsFeedRSS, LatestPublicationsFeedAtom

from journals import views as journals_views
from journals.regexes import ISSUE_DOI_LABEL_REGEX,\
    PUBLICATION_DOI_LABEL_REGEX, DOI_DISPATCH_PATTERN
from submissions import views as submission_views


favicon_view = RedirectView.as_view(
    url='/static/scipost/images/scipost_favicon.png', permanent=True)


app_name = 'scipost'


urlpatterns = [

    # redirect for favicon
    path(
        'favicon\.ico',
        favicon_view
    ),

    # Utilities:

    # Test Sentry installation
    path(
        'sentry-debug/',
        views.trigger_error,
        name='trigger_error'
    ),

    # Autocomplete
    path(
        'group-autocomplete',
        views.GroupAutocompleteView.as_view(),
        name='group-autocomplete'
    ),
    path(
        'user-autocomplete',
        views.UserAutocompleteView.as_view(),
        name='user-autocomplete'
    ),

    # Search
    path(
        'search',
        TemplateView.as_view(template_name='search/search.html'),
        name='search'
    ),

    # Homepage
    path(
        '',
        views.index,
        name='index'
    ),

    path(
        'home2',
        views.index2,
        name='index2'
    ),
    path(
        'home3',
        views.index3,
        name='index3'
    ),
    path(
        'home4',
        views.index4,
        name='index4'
    ),
    path(
        'home5',
        views.index5,
        name='index5'
    ),

    # Portal
    path(
        'portal',
        views.portal,
        name='portal'
    ),
    path(
        'portal2p2',
        views.portal2p2,
        name='portal2p2'
    ),

    # HTMX-delivered fragments
    path(
        'portal/_hx_home',
        views.portal_hx_home,
        name='portal_hx_home'
    ),
    path(
        'portal/_hx_home5',
        views.portal_hx_home5,
        name='portal_hx_home5'
    ),
    path(
        'portal/_hx_journals',
        TemplateView.as_view(template_name='scipost/portal/_hx_journals.html'),
        name='portal_hx_journals'
    ),
    path(
        'portal/_hx_publications',
        views.portal_hx_publications,
        name='portal_hx_publications'
    ),
    path(
        'portal/_hx_publications_page',
        views.portal_hx_publications_page,
        name='portal_hx_publications_page'
    ),
    path(
        'portal/_hx_submissions',
        views.portal_hx_submissions,
        name='portal_hx_submissions'
    ),
    path(
        'portal/_hx_submissions_page',
        views.portal_hx_submissions_page,
        name='portal_hx_submissions_page'
    ),
    path(
        'portal/_hx_reports',
        views.portal_hx_reports,
        name='portal_hx_reports'
    ),
    path(
        'portal/_hx_reports_page',
        views.portal_hx_reports_page,
        name='portal_hx_reports_page'
    ),
    path(
        'portal/_hx_comments',
        views.portal_hx_comments,
        name='portal_hx_comments'
    ),
    path(
        'portal/_hx_comments_page',
        views.portal_hx_comments_page,
        name='portal_hx_comments_page'
    ),
    path(
        '_hx_news',
        views._hx_news,
        name='_hx_news'
    ),
    path(
        '_hx_participates_in',
        TemplateView.as_view(template_name='scipost/_hx_participates_in.html'),
        name='_hx_participates_in'
    ),
    path(
        '_hx_sponsors',
        views._hx_sponsors,
        name='_hx_sponsors'
    ),

    path(
        'files/secure/<path:path>',
        views.protected_serve,
        name='secure_file'
    ),

    # General use pages
    path(
        'error',
        TemplateView.as_view(
            template_name='scipost/error.html'),
        name='error'
    ),
    path(
        'acknowledgement',
        TemplateView.as_view(
            template_name='scipost/acknowledgement.html'),
        name='acknowledgement'
    ),

    # Info
    path(
        'about',
        TemplateView.as_view(
            template_name='scipost/about.html'),
        name='about'
    ),
    path(
        'contact',
        TemplateView.as_view(template_name='scipost/contact.html'),
        name='contact'
    ),
    path(
        'call',
        TemplateView.as_view(
            template_name='scipost/call.html'),
        name='call'
    ),
    path(
        'donations/thank-you/',
        TemplateView.as_view(
            template_name='scipost/donation_thank_you.html'),
        name='donation_thank_you'
    ),
    path(
        'ExpSustDrive2018',
        TemplateView.as_view(template_name='scipost/ExpSustDrive2018.html'),
        name='ExpSustDrive2018'
    ),
    path(
        'PlanSciPost',
        TemplateView.as_view(template_name='scipost/PlanSciPost.html'),
        name='PlanSciPost'
    ),
    path(
        'foundation',
        TemplateView.as_view(template_name='scipost/foundation.html'),
        name='foundation'
    ),
    path(
        'tour',
        TemplateView.as_view(template_name='scipost/quick_tour.html'),
        name='quick_tour'
    ),
    path(
        'FAQ',
        TemplateView.as_view(template_name='scipost/FAQ.html'),
        name='FAQ'
    ),
    path(
        'terms_and_conditions',
        TemplateView.as_view(template_name='scipost/terms_and_conditions.html'),
        name='terms_and_conditions'
    ),
    path(
        'privacy_policy',
        TemplateView.as_view(template_name='scipost/privacy_policy.html'),
        name='privacy_policy'
    ),

    # Feeds
    path(
        'feeds',
        views.feeds,
        name='feeds'
    ),
    path(
        'rss/news/',
        LatestNewsFeedRSS(),
        name='feeds_rss_news'
    ),
    path(
        'atom/news/',
        LatestNewsFeedAtom(),
        name='feeds_atom_news'
    ),
    path(
        'rss/comments/',
        LatestCommentsFeedRSS(),
        name='feeds_rss_comments'
    ),
    path(
        'atom/comments/',
        LatestCommentsFeedAtom(),
        name='feeds_atom_comments'
    ),
    path(
        'rss/submissions/',
        LatestSubmissionsFeedRSS(),
        name='feeds_rss_submissions'
    ),
    path(
        'rss/submissions/<specialty:specialty>',
        LatestSubmissionsFeedRSS(),
        name='sub_feed_spec_rss'
    ),
    path(
        'atom/submissions/',
        LatestSubmissionsFeedAtom(),
        name='feeds_atom_submissions'
    ),
    path(
        'atom/submissions/<specialty:specialty>',
        LatestSubmissionsFeedAtom(),
        name='sub_feed_spec_atom'
    ),
    path(
        'rss/publications/',
        LatestPublicationsFeedRSS(),
        name='feeds_rss_publications'
    ),
    path(
        'rss/publications/<specialty:specialty>',
        LatestPublicationsFeedRSS(),
        name='pub_feed_spec_rss'
    ),
    path(
        'atom/publications/',
        LatestPublicationsFeedAtom(),
        name='feeds_atom_publications'
    ),
    path(
        'atom/publications/<specialty:specialty>',
        LatestPublicationsFeedAtom(),
        name='pub_feed_spec_atom'
    ),


    ################
    # Contributors:
    ################

    # Contributor info (public view)
    path(
        'contributor/<int:contributor_id>',
        views.contributor_info,
        name='contributor_info'
    ),

    # Registration
    path(
        'register',
        views.register,
        name='register'
    ),
    path(
        'thanks_for_registering',
        TemplateView.as_view(
            template_name='scipost/thanks_for_registering.html'),
        name='thanks_for_registering'
    ),
    path(
        'activation/<int:contributor_id>/<str:key>/',
        views.activation,
        name='activation'
    ),
    path(
        'activation/<int:contributor_id>/<str:key>/renew',
        views.request_new_activation_link,
        name='request_new_activation_link'
    ),
    path(
        'unsubscribe/<int:contributor_id>/<str:key>',
        views.unsubscribe,
        name='unsubscribe'
    ),
    path(
        'vet_registration_requests',
        views.vet_registration_requests,
        name='vet_registration_requests'
    ),
    path(
        'vet_registration_request_ack/<int:contributor_id>',
        views.vet_registration_request_ack,
        name='vet_registration_request_ack'
    ),
    path(
        'registration_requests',
        views.registration_requests,
        name='registration_requests'
    ),
    path(
        'registration_requests/<int:contributor_id>/reset',
        views.registration_requests_reset,
        name='registration_requests_reset'
    ),

    # Registration invitations (Never change this route! Thank you.)
    path(
        'invitation/<str:key>',
        views.invitation,
        name='invitation'
    ),

    # Authentication
    path(
        'login/',
        views.SciPostLoginView.as_view(),
        name='login'
    ),
    path(
        'login/info/',
        views.raw_user_auth_info,
        name='login_info'
    ),
    path(
        'logout/',
        views.SciPostLogoutView.as_view(),
        name='logout'
    ),
    path(
        'password_change',
        views.SciPostPasswordChangeView.as_view(),
        name='password_change'
    ),
    path(
        'password_reset/',
        views.SciPostPasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'reset/<uidb64>/<token>',
        views.SciPostPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'update_personal_data',
        views.update_personal_data,
        name='update_personal_data'
    ),
    path(
        'totp/',
        views.TOTPListView.as_view(),
        name='totp'
    ),
    path(
        'totp/create',
        views.TOTPDeviceCreateView.as_view(),
        name='totp_create'
    ),
    path(
        'totp/<int:device_id>/delete',
        views.TOTPDeviceDeleteView.as_view(),
        name='totp_delete'
    ),

    # Single sign-on [for GitLab: see api/urls]
    path(
        'sso_discourse',
        sso.discourse,
        name='sso_discourse'
    ),

    # Personal Page
    path(
        'personal_page/',
        views.personal_page,
        name='personal_page'
    ),
    path(
        'personal_page/account',
        views.personal_page,
        name='personal_page_account', kwargs={'tab': 'account'}
    ),
    path(
        'personal_page/admin_actions',
        views.personal_page,
        name='personal_page_admin_actions', kwargs={'tab': 'admin_actions'}
    ),
    path(
        'personal_page/editorial_actions',
        views.personal_page,
        name='personal_page_editorial_actions', kwargs={'tab': 'editorial_actions'}
    ),
    path(
        'personal_page/refereeing',
        views.personal_page,
        name='personal_page_refereeing', kwargs={'tab': 'refereeing'}
    ),
    path(
        'personal_page/publications',
        views.personal_page,
        name='personal_page_publications', kwargs={'tab': 'publications'}
    ),
    path(
        'personal_page/submissions',
        views.personal_page,
        name='personal_page_submissions', kwargs={'tab': 'submissions'}
    ),
    path(
        'personal_page/commentaries',
        views.personal_page,
        name='personal_page_commentaries', kwargs={'tab': 'commentaries'}
    ),
    path(
        'personal_page/theses',
        views.personal_page,
        name='personal_page_theses', kwargs={'tab': 'theses'}
    ),
    path(
        'personal_page/comments',
        views.personal_page,
        name='personal_page_comments', kwargs={'tab': 'comments'}
    ),
    path(
        'personal_page/author_replies',
        views.personal_page,
        name='personal_page_author_replies', kwargs={'tab': 'author_replies'}
    ),

    # Unavailabilities
    path(
        'unavailable_period',
        views.mark_unavailable_period,
        name='mark_unavailable_period'
    ),
    path(
        'unavailable_period/<int:period_id>/delete',
        views.delete_unavailable_period,
        name='delete_unavailable_period'
    ),

    # Authorship claims
    path(
        'claim_authorships',
        views.claim_authorships,
        name='claim_authorships'
    ),
    path(
        'claim_sub_authorship/<int:submission_id>/<int:claim>',
        views.claim_sub_authorship,
        name='claim_sub_authorship'
    ),
    path(
        'claim_com_authorship/<int:commentary_id>/<int:claim>',
        views.claim_com_authorship,
        name='claim_com_authorship'
    ),
    path(
        'claim_thesis_authorship/<int:thesis_id>/<int:claim>',
        views.claim_thesis_authorship,
        name='claim_thesis_authorship'
    ),
    path(
        'vet_authorship_claims',
        views.vet_authorship_claims,
        name='vet_authorship_claims'
    ),
    path(
        'vet_authorship_claim/<int:claim_id>/<int:claim>',
        views.vet_authorship_claim,
        name='vet_authorship_claim'
    ),

    # Potential duplicates
    path(
        'contributor_duplicates/',
        views.ContributorDuplicateListView.as_view(),
        name='contributor_duplicates'
    ),
    path(
        'contributor_merge/',
        views.contributor_merge,
        name='contributor_merge'
    ),

    ####################
    # Email facilities #
    ####################
    path(
        'email_group_members',
        views.email_group_members,
        name='email_group_members'
    ),
    path(
        'email_particular',
        views.email_particular,
        name='email_particular'
    ),
    path(
        'send_precooked_email',
        views.send_precooked_email,
        name='send_precooked_email'
    ),

    #####################
    # Editorial College #
    #####################
    path(
        'EdCol_by-laws',
        views.EdCol_bylaws,
        name='EdCol_by-laws'
    ),
    path(
        'EdCol_by-laws_Changes_2021_04',
        views.EdCol_bylaws_Changes_2021_04,
        name='EdCol_by-laws_Changes_2021_04'
    ),

    ################
    # Publications #
    ################

    # Reports
    path(
        '<report_doi_label:doi_label>',
        journals_views.report_detail,
        name='report_detail'
    ),

    # Comments
    path(
        '<comment_doi_label:doi_label>',
        journals_views.comment_detail,
        name='comment_detail'
    ),

    # Author Replies
    path(
        '<author_reply_doi_label:doi_label>',
        journals_views.author_reply_detail,
        name='author_reply_detail'
    ),

    # Publication detail (+pdf)
    re_path(
        '^10.21468/{pattern}$'.format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch,
        name='doi_dispatch'
    ),
    re_path(
        '^{pattern}$'.format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch,
        name='doi_dispatch'
    ),
    path(
        '10.21468/<publication_doi_label:doi_label>',
        journals_views.publication_detail,
        name='publication_detail'
    ),
    path(
        '<publication_doi_label:doi_label>',
        journals_views.publication_detail,
        name='publication_detail'
    ),
    path(
        '10.21468/<publication_doi_label:doi_label>/pdf',
        journals_views.publication_detail_pdf,
        name='publication_pdf'
    ),
    path(
        '<publication_doi_label:doi_label>/pdf',
        journals_views.publication_detail_pdf,
        name='publication_pdf'
    ),

    # Publication updates
    path(
        '<publication_doi_label:doi_label>-update-<int:update_nr>',
        journals_views.publication_update_detail,
        name='publication_update_detail'
    ),
    path(
        '10.21468/<publication_doi_label:doi_label>-update-<int:update_nr>',
        journals_views.publication_update_detail,
        name='publication_update_detail'
    ),


    # Journal issue
    path(
        '10.21468/<issue_doi_label:doi_label>',
        journals_views.issue_detail,
        name='issue_detail'
    ),
    path(
        '<issue_doi_label:doi_label>',
        journals_views.issue_detail,
        name='issue_detail'
    ),

    # Journal landing page
    path(
        '10.21468/<journal_doi_label:doi_label>',
        journals_views.landing_page,
        name='landing_page'
    ),
    path(
        '<journal_doi_label:doi_label>',
        journals_views.landing_page,
        name='landing_page'
    ),

    path(
        'arxiv_doi_feed/<journal_doi_label:doi_label>',
        journals_views.arxiv_doi_feed,
        name='arxiv_doi_feed'
    ),

    ################
    # Howto guides #
    ################

    path(
        'howto',
        TemplateView.as_view(template_name='scipost/howto.html'),
        name='howto'
    ),
    path(
        'howto/production',
        TemplateView.as_view(template_name='scipost/howto_production.html'),
        name='howto_production'
    ),


    ########################
    # Pwning verification #
    ########################

    path(
        'have-i-been-pwned-verification.txt',
        views.have_i_been_pwned,
        name='have_i_been_pwned'
    ),
]
