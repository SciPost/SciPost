from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView

from . import views
from .feeds import LatestCommentFeed

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^base$', views.base, name='base'),

    ## Info
    url(r'^about$', TemplateView.as_view(template_name='scipost/about.html'), name='about'),
    url(r'^tour$', TemplateView.as_view(template_name='scipost/quick_tour.html'), name='quick_tour'),
    url(r'^FAQ$', TemplateView.as_view(template_name='scipost/FAQ.html'), name='FAQ'),
    url(r'^terms_and_conditions$', TemplateView.as_view(template_name='scipost/terms_and_conditions.html'), name='terms_and_conditions'),
    url(r'^privacy_policy$', TemplateView.as_view(template_name='scipost/privacy_policy.html'), name='privacy_policy'),
    #url(r'^description$', views.description, name='description'),
    url(r'^peer_witnessed_refereeing$', TemplateView.as_view(template_name='scipost/peer_witnessed_refereeing.html'), name='peer_witnessed_refereeing'),

    # Search 
    url(r'^search$', views.search, name='search'),


    ################
    # Contributors:
    ################

    ## Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$', TemplateView.as_view(template_name='scipost/thanks_for_registering.html'), name='thanks_for_registering'),
    url(r'^activation/(?P<key>.+)$', views.activation, name='activation'),
    url(r'^activation_ack$', TemplateView.as_view(template_name='scipost/activation_ack.html'), name='activation_ack'),
    url(r'^request_new_activation_link/(?P<oldkey>.+)$', views.request_new_activation_link, name='request_new_activation_link'),
    url(r'^request_new_activation_link_ack$', TemplateView.as_view(template_name='scipost/request_new_activation_link_ack.html'), name='request_new_activation_link_ack'),
    url(r'^already_activated$', TemplateView.as_view(template_name='scipost/already_activated.html'), name='already_activated'),
    url(r'^vet_registration_requests$', views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$', views.vet_registration_request_ack, name='vet_registration_request_ack'),
    url(r'^registration_invitations$', views.registration_invitations, name="registration_invitations"),
    url(r'^registration_invitation_sent$', TemplateView.as_view(template_name='scipost/registration_invitation_sent.html'), name='registration_invitation_sent'),
    #url(r'^invitation/(?P<key>.+)$', views.accept_invitation, name='accept_invitation'),
    url(r'^invitation/(?P<key>.+)$', views.invitation, name='invitation'),
    url(r'^accept_invitation_error$', TemplateView.as_view(template_name='scipost/accept_invitation_error.html'), name='accept_invitation_error'),

    ## Authentication
    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^personal_page$', views.personal_page, name='personal_page'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', views.reset_password_confirm, name='reset_password_confirm'),
    url(r'^reset_password/$', views.reset_password, name='reset_password'),
    url(r'^update_personal_data$', views.update_personal_data, name='update_personal_data'),
    url(r'^update_personal_data_ack$', TemplateView.as_view(template_name='scipost/update_personal_data_ack.html'), name='update_personal_data_ack'),

    # Contributor info
    url(r'^(?P<contributor_id>[0-9]+)$', views.contributor_info, name="contributor_info"),

    # Authorship claims
    url(r'^claim_authorships$', views.claim_authorships, name="claim_authorships"),
    url(r'^claim_sub_authorship/(?P<submission_id>[0-9]+)/(?P<claim>[0-1])$', views.claim_sub_authorship, name='claim_sub_authorship'),
    url(r'^claim_com_authorship/(?P<commentary_id>[0-9]+)/(?P<claim>[0-1])$', views.claim_com_authorship, name='claim_com_authorship'),
    url(r'^claim_thesis_authorship/(?P<thesis_id>[0-9]+)/(?P<claim>[0-1])$', views.claim_thesis_authorship, name='claim_thesis_authorship'),
    url(r'^vet_authorship_claims$', views.vet_authorship_claims, name="vet_authorship_claims"),
    url(r'^vet_authorship_claim/(?P<claim_id>[0-9]+)/(?P<claim>[0-1])$', views.vet_authorship_claim, name='vet_authorship_claim'),

    # Lists
    url(r'^create_list$', views.create_list, name='create_list'),
    url(r'^list/(?P<list_id>[0-9]+)$', views.list, name='list'),
    url(r'^list_add_element/(?P<list_id>[0-9]+)/(?P<type>[SCTc])/(?P<element_id>[0-9]+)$', views.list_add_element, name='list_add_element'),

    # Feeds
    url(r'^latest_comment/feed/$', LatestCommentFeed()),

    # Teams
    url(r'^create_team$', views.create_team, name='create_team'),
    url(r'^add_team_member/(?P<team_id>[0-9]+)$', views.add_team_member, name='add_team_member'),
    url(r'^add_team_member/(?P<team_id>[0-9]+)/(?P<contributor_id>[0-9]+)$', views.add_team_member, name='add_team_member'),

    # Graphs
    url(r'^create_graph$', views.create_graph, name='create_graph'),
    url(r'^graph/(?P<graph_id>[0-9]+)$', views.graph, name='graph'),
    url(r'^edit_graph_node/(?P<node_id>[0-9]+)$', views.edit_graph_node, name='edit_graph_node'),
    url(r'^api/graph/(?P<graph_id>[0-9]+)$', views.api_graph, name='api_graph'),
]
