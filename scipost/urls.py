from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views
from .feeds import LatestNewsFeedRSS, LatestNewsFeedAtom, LatestCommentsFeedRSS, LatestCommentsFeedAtom, LatestSubmissionsFeedRSS, LatestSubmissionsFeedAtom, LatestPublicationsFeedRSS, LatestPublicationsFeedAtom

from journals import views as journals_views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^base$', views.base, name='base'),

    # General use pages
    url(r'^error$', TemplateView.as_view(template_name='scipost/error.html'), name='error'),
    url(r'^acknowledgement$', TemplateView.as_view(template_name='scipost/acknowledgement.html'),
        name='acknowledgement'),

    ## Info
    url(r'^about$', TemplateView.as_view(template_name='scipost/about.html'), name='about'),
    url(r'^call$', TemplateView.as_view(template_name='scipost/call.html'), name='call'),
    url(r'^foundation$', TemplateView.as_view(template_name='scipost/foundation.html'),
        name='foundation'),
    url(r'^tour$', TemplateView.as_view(template_name='scipost/quick_tour.html'), name='quick_tour'),
    url(r'^FAQ$', TemplateView.as_view(template_name='scipost/FAQ.html'), name='FAQ'),
    url(r'^terms_and_conditions$',
        TemplateView.as_view(template_name='scipost/terms_and_conditions.html'),
        name='terms_and_conditions'),
    url(r'^privacy_policy$', TemplateView.as_view(template_name='scipost/privacy_policy.html'),
        name='privacy_policy'),

    # Feeds
    url(r'^feeds$', views.feeds, #TemplateView.as_view(template_name='scipost/feeds.html'),
        name='feeds'),
    url(r'^rss/news/$', LatestNewsFeedRSS()),
    url(r'^atom/news/$', LatestNewsFeedAtom()),
    url(r'^rss/comments/$', LatestCommentsFeedRSS()),
    url(r'^atom/comments/$', LatestCommentsFeedAtom()),
    url(r'^rss/submissions/$',
        LatestSubmissionsFeedRSS()),
    url(r'^rss/submissions/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestSubmissionsFeedRSS(),
        name='sub_feed_spec_rss'),
    url(r'^atom/submissions/$',
        LatestSubmissionsFeedAtom()),
    url(r'^atom/submissions/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestSubmissionsFeedAtom(),
        name='sub_feed_spec_atom'),
    url(r'^rss/publications/$',
        LatestPublicationsFeedRSS()),
    url(r'^rss/publications/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestPublicationsFeedRSS(),
        name='pub_feed_spec_rss'),
    url(r'^atom/publications/$',
        LatestPublicationsFeedAtom()),
    url(r'^atom/publications/(?P<subject_area>[a-zA-Z]+:[A-Z]{2,})$',
        LatestPublicationsFeedAtom(),
        name='pub_feed_spec_atom'),

    # Search
    url(r'^search$', views.search, name='search'),
    url(r'^search/', include('haystack.urls')),

    ################
    # Contributors:
    ################

    ## Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$',
        TemplateView.as_view(template_name='scipost/thanks_for_registering.html'),
        name='thanks_for_registering'),
    url(r'^activation/(?P<key>.+)$', views.activation, name='activation'),
    url(r'^request_new_activation_link/(?P<oldkey>.+)$',
        views.request_new_activation_link,
        name='request_new_activation_link'),
    url(r'^already_activated$',
        TemplateView.as_view(template_name='scipost/already_activated.html'),
        name='already_activated'),
    url(r'^unsubscribe/(?P<key>.+)$', views.unsubscribe, name='unsubscribe'),
    url(r'^unsubscribe_confirm/(?P<key>.+)$',
        views.unsubscribe_confirm, name='unsubscribe_confirm'),
    url(r'^vet_registration_requests$',
        views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$',
        views.vet_registration_request_ack, name='vet_registration_request_ack'),
    url(r'^registration_invitations/(?P<draft_id>[0-9]+)$',
        views.registration_invitations, name="registration_invitations_from_draft"),
    url(r'^registration_invitations$',
        views.registration_invitations, name="registration_invitations"),
    url(r'^draft_registration_invitation$',
        views.draft_registration_invitation, name="draft_registration_invitation"),
    url(r'^edit_draft_reg_inv/(?P<draft_id>[0-9]+)$',
        views.edit_draft_reg_inv, name="edit_draft_reg_inv"),
    url(r'^map_draft_reg_inv_to_contributor/(?P<draft_id>[0-9]+)/(?P<contributor_id>[0-9]+)$',
        views.map_draft_reg_inv_to_contributor, name="map_draft_reg_inv_to_contributor"),
    url(r'^registration_invitations_cleanup$',
        views.registration_invitations_cleanup,
        name="registration_invitations_cleanup"),
    url(r'^remove_registration_invitation/(?P<invitation_id>[0-9]+)$',
        views.remove_registration_invitation,
        name="remove_registration_invitation"),
    url(r'^edit_invitation_personal_message/(?P<invitation_id>[0-9]+)$',
        views.edit_invitation_personal_message,
        name="edit_invitation_personal_message"),
    url(r'^renew_registration_invitation/(?P<invitation_id>[0-9]+)$',
        views.renew_registration_invitation,
        name="renew_registration_invitation"),
    url(r'^mark_reg_inv_as_declined/(?P<invitation_id>[0-9]+)$',
        views.mark_reg_inv_as_declined,
        name="mark_reg_inv_as_declined"),
    url(r'^registration_invitation_sent$',
        TemplateView.as_view(template_name='scipost/registration_invitation_sent.html'),
        name='registration_invitation_sent'),
    #url(r'^invitation/(?P<key>.+)$', views.accept_invitation, name='accept_invitation'),
    url(r'^invitation/(?P<key>.+)$', views.invitation, name='invitation'),
    url(r'^accept_invitation_error$',
        TemplateView.as_view(template_name='scipost/accept_invitation_error.html'),
        name='accept_invitation_error'),
    url(r'^mark_draft_inv_as_processed/(?P<draft_id>[0-9]+)$',
        views.mark_draft_inv_as_processed, name='mark_draft_inv_as_processed'),
    url(r'^citation_notifications$',
        views.citation_notifications, name='citation_notifications'),
    url(r'^process_citation_notification/(?P<cn_id>[0-9]+)$',
        views.process_citation_notification, name='process_citation_notification'),

    ## Authentication
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^personal_page$', views.personal_page, name='personal_page'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        views.reset_password_confirm, name='reset_password_confirm'),
    url(r'^reset_password/$', views.reset_password, name='reset_password'),
    url(r'^update_personal_data$', views.update_personal_data, name='update_personal_data'),

    # Unavailabilities
    url(r'^mark_unavailable_period$', views.mark_unavailable_period, name='mark_unavailable_period'),

    # Contributor info
    url(r'^(?P<contributor_id>[0-9]+)$', views.contributor_info, name="contributor_info"),

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
    url(r'^Fellow_activity_overview/(?P<Fellow_id>[0-9]+)$',
        views.Fellow_activity_overview,
        name='Fellow_activity_overview'),
    url(r'^Fellow_activity_overview$',
        views.Fellow_activity_overview,
        name='Fellow_activity_overview'),

    ############################
    # Virtual General Meetings #
    ############################
    url(r'^VGMs$', views.VGMs, name='VGMs'),
    url(r'^VGM/(?P<VGM_id>[0-9]+)/$', views.VGM_detail, name='VGM_detail'),
    url(r'^feedback/(?P<VGM_id>[0-9]+)$',
        views.feedback, name='feedback'),
    url(r'^add_remark_on_feedback/(?P<VGM_id>[0-9]+)/(?P<feedback_id>[0-9]+)$',
        views.add_remark_on_feedback, name='add_remark_on_feedback'),
    url(r'^nominate_Fellow/(?P<VGM_id>[0-9]+)$',
        views.nominate_Fellow, name='nominate_Fellow'),
    url(r'^add_remark_on_nomination/(?P<VGM_id>[0-9]+)/(?P<nomination_id>[0-9]+)$',
        views.add_remark_on_nomination, name='add_remark_on_nomination'),
    url(r'^vote_on_nomination/(?P<nomination_id>[0-9]+)/(?P<vote>[AND])$',
        views.vote_on_nomination, name='vote_on_nomination'),
    url(r'^put_motion_forward/(?P<VGM_id>[0-9]+)$',
        views.put_motion_forward, name='put_motion_forward'),
    url(r'^add_remark_on_motion/(?P<motion_id>[0-9]+)$',
        views.add_remark_on_motion, name='add_remark_on_motion'),
    url(r'^vote_on_motion/(?P<motion_id>[0-9]+)/(?P<vote>[AND])$',
        views.vote_on_motion, name='vote_on_motion'),

    ################
    # Publications #
    ################

    url(r'^SciPostPhys$',
        journals_views.scipost_physics,
        name='SciPostPhys'),
    url(r'^10.21468/SciPostPhys$',
        journals_views.scipost_physics,
        name='doi_SciPostPhys'),
    url(r'^SciPostPhys.(?P<volume_nr>[0-9]+).(?P<issue_nr>[0-9]+)$',
        journals_views.scipost_physics_issue_detail,
        name='SciPostPhys_issue_detail_from_doi_label'),
    url(r'^10.21468/SciPostPhys.(?P<volume_nr>[0-9]+).(?P<issue_nr>[0-9]+)$',
        journals_views.scipost_physics_issue_detail,
        name='SciPostPhys_issue_detail'),

    url(r'^(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.publication_detail,
        name='publication_detail'),
    url(r'^(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/pdf$',
        journals_views.publication_pdf,
        name='publication_pdf'),
    url(r'^(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.publication_detail_from_doi_label,
        name='publication_detail_from_doi_label'),
    url(r'^(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/pdf$',
        journals_views.publication_pdf_from_doi_label,
        name='publication_pdf_from_doi_label'),


    ################
    # Howto guides #
    ################

    url(r'^howto$',
        TemplateView.as_view(template_name='scipost/howto.html'),
        name='howto'),
    url(r'^howto/production$',
        TemplateView.as_view(template_name='scipost/howto_production.html'),
        name='howto_production'),


    #############################
    # Supporting Partners Board #
    #############################

    url(r'^supporting_partners$', views.supporting_partners,
        name='supporting_partners'),
    url(r'^SPB_membership_request$', views.SPB_membership_request,
        name='SPB_membership_request'),

]
