from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Commentaries
    url(r'^$', views.commentaries, name='commentaries'),
    url(r'^browse/(?P<discipline>[a-z]+)/(?P<nrweeksback>[0-9]+)/$', views.browse, name='browse'),
    url(r'^howto$', TemplateView.as_view(template_name='commentaries/howto.html'), name='howto'),

    # Match a DOI-based link:
    url(r'^(?P<arxiv_or_DOI_string>10.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+)/$', views.commentary_detail, name='commentary'),
    # Match an arxiv-based link:
    # new style identifiers:
    url(r'^(?P<arxiv_or_DOI_string>arXiv:[0-9]{4,}.[0-9]{5,}(v[0-9]+)?)/$', views.commentary_detail, name='commentary'),
    # old style identifiers:
    url(r'^(?P<arxiv_or_DOI_string>arXiv:[a-z-]+/[0-9]{7,}(v[0-9]+)?)/$', views.commentary_detail, name='commentary'),

    url(r'^request_commentary$', views.RequestCommentary.as_view(), name='request_commentary'),
    url(r'^prefill_using_DOI$', views.prefill_using_DOI, name='prefill_using_DOI'),
    url(r'^prefill_using_identifier$', views.PrefillUsingIdentifierView.as_view(), name='prefill_using_identifier'),
    url(r'^vet_commentary_requests$', views.vet_commentary_requests, name='vet_commentary_requests'),
    url(r'^vet_commentary_request_ack/(?P<commentary_id>[0-9]+)$', views.vet_commentary_request_ack, name='vet_commentary_request_ack'),
]
