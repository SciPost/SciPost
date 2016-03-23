from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^base$', views.base, name='base'),

    ## Info
    url(r'^about$', TemplateView.as_view(template_name='scipost/about.html'), name='about'),
    url(r'^FAQ$', TemplateView.as_view(template_name='scipost/FAQ.html'), name='FAQ'),
    #url(r'^description$', views.description, name='description'),
    url(r'^peer_witnessed_refereeing$', TemplateView.as_view(template_name='scipost/peer_witnessed_refereeing.html'), name='peer_witnessed_refereeing'),

    ################
    # Contributors:
    ################

    ## Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$', TemplateView.as_view(template_name='scipost/thanks_for_registering.html'), name='thanks for registering'),
    url(r'^activation/(?P<key>.+)$', views.activation, name='activation'),
    url(r'^activation_ack$', TemplateView.as_view(template_name='scipost/activation_ack.html'), name='activation_ack'),
    url(r'^request_new_activation_link/(?P<oldkey>.+)$', views.request_new_activation_link, name='request_new_activation_link'),
    url(r'^request_new_activation_link_ack$', TemplateView.as_view(template_name='scipost/request_new_activation_link_ack.html'), name='request_new_activation_link_ack'),
    url(r'^already_activated$', TemplateView.as_view(template_name='scipost/already_activated.html'), name='already_activated'),
    url(r'^vet_registration_requests$', views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$', views.vet_registration_request_ack, name='vet_registration_request_ack'),

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
]
