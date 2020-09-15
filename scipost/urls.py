__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.contrib.auth.decorators import permission_required
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.urls import include, path, re_path

from . import views
from .feeds import LatestNewsFeedRSS, LatestNewsFeedAtom, LatestCommentsFeedRSS,\
                   LatestCommentsFeedAtom, LatestSubmissionsFeedRSS, LatestSubmissionsFeedAtom,\
                   LatestPublicationsFeedRSS, LatestPublicationsFeedAtom

from journals import views as journals_views
from journals.regexes import JOURNAL_DOI_LABEL_REGEX, ISSUE_DOI_LABEL_REGEX,\
    PUBLICATION_DOI_LABEL_REGEX, DOI_DISPATCH_PATTERN
from submissions import views as submission_views


favicon_view = RedirectView.as_view(
    url='/static/scipost/images/scipost_favicon.png', permanent=True)

JOURNAL_PATTERN = '(?P<doi_label>%s)' % JOURNAL_DOI_LABEL_REGEX

app_name = 'scipost'


urlpatterns = [


    # redirect for favicon
    re_path(r'^favicon\.ico$', favicon_view),

    # Utilities:

    # Test Sentry installation
    url(r'sentry-debug/$', views.trigger_error, name='trigger_error'),

    # Autocomplete
    path(
        'group-autocomplete',
        views.GroupAutocompleteView.as_view(),
        name='group-autocomplete'
    ),

    # Search
    url(r'^search', views.SearchView.as_view(), name='search'),
    url(r'^$', views.index, name='index'),
    url(r'^files/secure/(?P<path>.*)$', views.protected_serve, name='secure_file'),

    # General use pages
    url(r'^error$', TemplateView.as_view(template_name='scipost/error.html'), name='error'),
    url(r'^acknowledgement$', TemplateView.as_view(template_name='scipost/acknowledgement.html'),
        name='acknowledgement'),

    # Info
    url(r'^about$', TemplateView.as_view(template_name='scipost/about.html'), name='about'),
    url(r'^call$', TemplateView.as_view(template_name='scipost/call.html'), name='call'),
    url(r'^donations/thank-you/$', TemplateView.as_view(template_name='scipost/donation_thank_you.html'), name='donation_thank_you'),
    url(
        r'^ExpSustDrive2018$',
        TemplateView.as_view(template_name='scipost/ExpSustDrive2018.html'),
        name='ExpSustDrive2018'
    ),
    url(
        r'^PlanSciPost$',
        TemplateView.as_view(template_name='scipost/PlanSciPost.html'),
        name='PlanSciPost'
    ),
    url(r'^foundation$', TemplateView.as_view(template_name='scipost/foundation.html'),
        name='foundation'),
    url(r'^tour$', TemplateView.as_view(template_name='scipost/quick_tour.html'),
        name='quick_tour'),
    url(r'^FAQ$', TemplateView.as_view(template_name='scipost/FAQ.html'), name='FAQ'),
    url(r'^terms_and_conditions$',
        TemplateView.as_view(template_name='scipost/terms_and_conditions.html'),
        name='terms_and_conditions'),
    url(r'^privacy_policy$', TemplateView.as_view(template_name='scipost/privacy_policy.html'),
        name='privacy_policy'),

    # Feeds
    url(r'^feeds$', views.feeds, name='feeds'),
    url(r'^rss/news/$', LatestNewsFeedRSS(), name='feeds_rss_news'),
    url(r'^atom/news/$', LatestNewsFeedAtom(), name='feeds_atom_news'),
    url(r'^rss/comments/$', LatestCommentsFeedRSS(), name='feeds_rss_comments'),
    url(r'^atom/comments/$', LatestCommentsFeedAtom(), name='feeds_atom_comments'),
    url(r'^rss/submissions/$', LatestSubmissionsFeedRSS(), name='feeds_rss_submissions'),
    url(r'^rss/submissions/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestSubmissionsFeedRSS(),
        name='sub_feed_spec_rss'),
    url(r'^atom/submissions/$', LatestSubmissionsFeedAtom(), name='feeds_atom_submissions'),
    url(r'^atom/submissions/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestSubmissionsFeedAtom(),
        name='sub_feed_spec_atom'),
    url(r'^rss/publications/$', LatestPublicationsFeedRSS(), name='feeds_rss_publications'),
    url(r'^rss/publications/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestPublicationsFeedRSS(),
        name='pub_feed_spec_rss'),
    url(r'^atom/publications/$', LatestPublicationsFeedAtom(), name='feeds_atom_publications'),
    url(r'^atom/publications/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestPublicationsFeedAtom(),
        name='pub_feed_spec_atom'),


    ################
    # Contributors:
    ################

    # Contributor info (public view)
    url(r'^contributor/(?P<contributor_id>[0-9]+)$', views.contributor_info,
        name="contributor_info"),

    # Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$',
        TemplateView.as_view(template_name='scipost/thanks_for_registering.html'),
        name='thanks_for_registering'),
    url(r'^activation/(?P<contributor_id>[0-9]+)/(?P<key>.+)/$',
        views.activation, name='activation'),
    url(r'^activation/(?P<contributor_id>[0-9]+)/(?P<key>.+)/renew$',
        views.request_new_activation_link, name='request_new_activation_link'),
    url(r'^unsubscribe/(?P<contributor_id>[0-9]+)/(?P<key>.+)$', views.unsubscribe,
        name='unsubscribe'),
    url(r'^vet_registration_requests$',
        views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$',
        views.vet_registration_request_ack, name='vet_registration_request_ack'),
    url(r'^registration_requests$', views.registration_requests, name="registration_requests"),
    url(r'^registration_requests/(?P<contributor_id>[0-9]+)/reset$',
        views.registration_requests_reset, name="registration_requests_reset"),

    # Registration invitations (Never change this route! Thank you.)
    url(r'^invitation/(?P<key>.+)$', views.invitation, name='invitation'),

    # Authentication
    url(
        r'^login/$',
        views.SciPostLoginView.as_view(),
        name='login'
    ),
    url(
        r'^login/info/$',
        views.raw_user_auth_info,
        name='login_info'
    ),
    url(
        r'^logout/$',
        views.SciPostLogoutView.as_view(),
        name='logout'
    ),
    url(
        r'^password_change$',
        views.SciPostPasswordChangeView.as_view(),
        name='password_change'
    ),
    url(
        r'^password_reset/$',
        views.SciPostPasswordResetView.as_view(),
        name='password_reset'
    ),
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.SciPostPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    url(r'^update_personal_data$', views.update_personal_data, name='update_personal_data'),
    url(r'^totp/$', views.TOTPListView.as_view(), name='totp'),
    url(r'^totp/create$', views.TOTPDeviceCreateView.as_view(), name='totp_create'),
    url(r'^totp/(?P<device_id>[0-9]+)/delete$', views.TOTPDeviceDeleteView.as_view(), name='totp_delete'),

    # Personal Page
    url(r'^personal_page/$', views.personal_page, name='personal_page'),
    url(r'^personal_page/account$', views.personal_page,
        name='personal_page_account', kwargs={'tab': 'account'}),
    url(r'^personal_page/admin_actions$', views.personal_page,
        name='personal_page_admin_actions', kwargs={'tab': 'admin_actions'}),
    url(r'^personal_page/editorial_actions$', views.personal_page,
        name='personal_page_editorial_actions', kwargs={'tab': 'editorial_actions'}),
    url(r'^personal_page/refereeing$', views.personal_page,
        name='personal_page_refereeing', kwargs={'tab': 'refereeing'}),
    url(r'^personal_page/publications$', views.personal_page,
        name='personal_page_publications', kwargs={'tab': 'publications'}),
    url(r'^personal_page/submissions$', views.personal_page,
        name='personal_page_submissions', kwargs={'tab': 'submissions'}),
    url(r'^personal_page/commentaries$', views.personal_page,
        name='personal_page_commentaries', kwargs={'tab': 'commentaries'}),
    url(r'^personal_page/theses$', views.personal_page,
        name='personal_page_theses', kwargs={'tab': 'theses'}),
    url(r'^personal_page/comments$', views.personal_page,
        name='personal_page_comments', kwargs={'tab': 'comments'}),
    url(r'^personal_page/author_replies$', views.personal_page,
        name='personal_page_author_replies', kwargs={'tab': 'author_replies'}),

    # Unavailabilities
    url(r'^unavailable_period$', views.mark_unavailable_period, name='mark_unavailable_period'),
    url(r'^unavailable_period/(?P<period_id>[0-9]+)/delete$', views.delete_unavailable_period,
        name='delete_unavailable_period'),

    # Authorship claims
    url(r'^claim_authorships$', views.claim_authorships, name="claim_authorships"),
    url(r'^claim_sub_authorship/(?P<submission_id>[0-9]+)/(?P<claim>[0-1])$',
        views.claim_sub_authorship, name='claim_sub_authorship'),
    url(r'^claim_com_authorship/(?P<commentary_id>[0-9]+)/(?P<claim>[0-1])$',
        views.claim_com_authorship, name='claim_com_authorship'),
    url(r'^claim_thesis_authorship/(?P<thesis_id>[0-9]+)/(?P<claim>[0-1])$',
        views.claim_thesis_authorship, name='claim_thesis_authorship'),
    url(r'^vet_authorship_claims$', views.vet_authorship_claims, name="vet_authorship_claims"),
    url(r'^vet_authorship_claim/(?P<claim_id>[0-9]+)/(?P<claim>[0-1])$',
        views.vet_authorship_claim, name='vet_authorship_claim'),

    # Potential duplicates
    url(r'contributor_duplicates/$',
        views.ContributorDuplicateListView.as_view(),
        name='contributor_duplicates'),
    url(r'contributor_merge/$',
        views.contributor_merge,
        name='contributor_merge'),

    ####################
    # Email facilities #
    ####################
    url('^email_group_members$', views.email_group_members, name='email_group_members'),
    url('^email_particular$', views.email_particular, name='email_particular'),
    url('^send_precooked_email$', views.send_precooked_email, name='send_precooked_email'),

    #####################
    # Editorial College #
    #####################
    url(r'^EdCol_by-laws$', views.EdCol_bylaws, name='EdCol_by-laws'),

    ################
    # Publications #
    ################

    # Reports
    url(r'^(?P<doi_label>SciPost.Report.[0-9]+)$',
        journals_views.report_detail,
        name='report_detail'),
    url(r'^10.21468/(?P<doi_label>SciPost.Report.[0-9]+)$',
        journals_views.report_detail,
        name='report_detail'),

    # Comments
    url(r'^(?P<doi_label>SciPost.Comment.[0-9]+)$',
        journals_views.comment_detail,
        name='comment_detail'),
    url(r'^10.21468/(?P<doi_label>SciPost.Comment.[0-9]+)$',
        journals_views.comment_detail,
        name='comment_detail'),

    # Author Replies
    url(r'^(?P<doi_label>SciPost.AuthorReply.[0-9]+)$',
        journals_views.author_reply_detail,
        name='author_reply_detail'),
    url(r'^10.21468/(?P<doi_label>SciPost.AuthorReply.[0-9]+)$',
        journals_views.author_reply_detail,
        name='author_reply_detail'),

    # Publication detail (+pdf)
    url(r'^10.21468/{pattern}$'.format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch, name='doi_dispatch'),
    url(r'^{pattern}$'.format(pattern=DOI_DISPATCH_PATTERN),
        journals_views.doi_dispatch, name='doi_dispatch'),
    url(r'^10.21468/(?P<doi_label>{regex})$'.format(regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_detail,
        name='publication_detail'),
    url(r'^(?P<doi_label>{regex})$'.format(regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_detail,
        name='publication_detail'),
    url(r'^10.21468/(?P<doi_label>{regex})/pdf$'.format(regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_detail_pdf,
        name='publication_pdf'),
    url(r'^(?P<doi_label>{regex})/pdf$'.format(regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_detail_pdf,
        name='publication_pdf'),

    # Publication updates
    url(r'^(?P<doi_label>{regex})-update-(?P<update_nr>[0-9]+)$'.format(
        regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_update_detail,
        name='publication_update_detail'),
    url(r'^10.21468/(?P<doi_label>{regex})-update-(?P<update_nr>[0-9]+)$'.format(
        regex=PUBLICATION_DOI_LABEL_REGEX),
        journals_views.publication_update_detail,
        name='publication_update_detail'),


    # Journal issue
    url(r'^10.21468/(?P<doi_label>{regex})$'.format(regex=ISSUE_DOI_LABEL_REGEX),
        journals_views.issue_detail, name='issue_detail'),
    url(r'^(?P<doi_label>{regex})$'.format(regex=ISSUE_DOI_LABEL_REGEX),
        journals_views.issue_detail, name='issue_detail'),

    # Journal landing page
    url(r'^10.21468/%s$' % JOURNAL_PATTERN,
        journals_views.landing_page, name='landing_page'),
    url(r'^%s$' % JOURNAL_PATTERN,
        journals_views.landing_page, name='landing_page'),
    url(r'^arxiv_doi_feed/%s' % JOURNAL_PATTERN,
        journals_views.arxiv_doi_feed, name='arxiv_doi_feed'),

    ################
    # Howto guides #
    ################

    url(r'^howto$',
        TemplateView.as_view(template_name='scipost/howto.html'),
        name='howto'),
    url(r'^howto/production$',
        TemplateView.as_view(template_name='scipost/howto_production.html'),
        name='howto_production'),

    # Temporary fix, due to mails sent with wrong urls
    url(r'^decline_ref_invitation/(?P<invitation_key>.+)$',
        submission_views.decline_ref_invitation),


    ########################
    # Pawning verification #
    ########################

    url(r'^have-i-been-pwned-verification.txt$',
        views.have_i_been_pwned,
        name='have_i_been_pwned'),
]
