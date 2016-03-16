from django.conf.urls import include, url
from django.views.generic import TemplateView 

from . import views

urlpatterns = [
    # Commentaries
    url(r'^$', views.commentaries, name='commentaries'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^howto$', TemplateView.as_view(template_name='commentaries/howto.html'), name='howto'),
    url(r'^commentary/(?P<commentary_id>[0-9]+)/$', views.commentary_detail, name='commentary'),
    url(r'^request_commentary$', views.request_commentary, name='request_commentary'),
    url(r'^request_commentary_ack$', TemplateView.as_view(template_name='commentaries/request_commentary_ack.html'), name='request_commentary_ack'),
    url(r'^vet_commentary_requests$', views.vet_commentary_requests, name='vet_commentary_requests'),
    url(r'^vet_commentary_request_ack/(?P<commentary_id>[0-9]+)$', views.vet_commentary_request_ack, name='vet_commentary_request_ack'),
]
