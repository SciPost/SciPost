from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^base$', views.base, name='base'),
    # Info
    url(r'^about$', views.about, name='about'),
    url(r'^description$', views.description, name='description'),
    url(r'^peer_witnessed_refereeing$', views.peer_witnessed_refereeing, name='peer_witnessed_refereeing'),
    ################
    # Contributors:
    ################
    ## Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$', views.thanks_for_registering, name='thanks for registering'),
    url(r'^vet_registration_requests$', views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$', views.vet_registration_request_ack, name='vet_registration_request_ack'),
    ## Authentication
    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^personal_page$', views.personal_page, name='personal_page'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^change_password_ack$', views.change_password_ack, name='change_password_ack'),
    url(r'^update_personal_data$', views.update_personal_data, name='update_personal_data'),
    url(r'^update_personal_data_ack$', views.update_personal_data_ack, name='update_personal_data_ack'),
]
