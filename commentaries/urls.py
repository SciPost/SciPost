from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Commentaries
    url(r'^$', views.commentaries, name='commentaries'),
    url(r'^commentary/(?P<commentary_id>[0-9]+)/$', views.commentary_detail, name='commentary'),
    url(r'^request_commentary$', views.request_commentary, name='request_commentary'),
    url(r'^request_commentary_ack$', views.request_commentary_ack, name='request_commentary_ack'),
    url(r'^vet_commentary_requests$', views.vet_commentary_requests, name='vet_commentary_requests'),
    url(r'^no_commentary_req_to_vet$', views.no_commentary_req_to_vet, name='no_commentary_req_to_vet'),
    url(r'^vet_commentary_request_ack/(?P<commentary_id>[0-9]+)$', views.vet_commentary_request_ack, name='vet_commentary_request_ack'),
]
