from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Thesis Links
    url(r'^$', views.theses, name='theses'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^(?P<thesislink_id>[0-9]+)/$', views.thesis_detail, name='thesis'),
    url(r'^request_thesislink$', views.RequestThesisLink.as_view(), name='request_thesislink'),
    url(r'^vet_thesislink_requests$', views.VetThesisLinkRequests.as_view(),
        name='vet_thesislink_requests'),
    url(r'^vet_thesislink_request_ack/(?P<thesislink_id>[0-9]+)$',
        views.vet_thesislink_request_ack, name='vet_thesislink_request_ack'),
]
