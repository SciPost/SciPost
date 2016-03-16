from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Thesis Links
    url(r'^$', views.theses, name='theses'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^thesis/(?P<thesislink_id>[0-9]+)/$', views.thesis_detail, name='thesis'),
    url(r'^request_thesislink$', views.request_thesislink, name='request_thesislink'),
    url(r'^request_thesislink_ack$', TemplateView.as_view(template_name='theses/request_thesislink_ack.html'), name='request_thesislink_ack'),
    url(r'^vet_thesislink_requests$', views.vet_thesislink_requests, name='vet_thesislink_requests'),
    url(r'^vet_thesislink_request_ack/(?P<thesislink_id>[0-9]+)$', views.vet_thesislink_request_ack, name='vet_thesislink_request_ack'),
]
