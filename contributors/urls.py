from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$', views.thanks_for_registering, name='thanks for registering'),
    url(r'^vet_registration_requests$', views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$', views.vet_registration_request_ack, name='vet_registration_request_ack'),
    # Authentication
    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^personal_page$', views.personal_page, name='personal_page'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^change_password_ack$', views.change_password_ack, name='change_password_ack'),
]
