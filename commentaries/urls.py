__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'commentaries'

urlpatterns = [
    # Commentaries
    url(r'^$', views.CommentaryListView.as_view(), name='commentaries'),
    url(r'^browse/(?P<nrweeksback>[0-9]{1,3})/$',
        views.CommentaryListView.as_view(), name='browse'),
    url(r'^howto$', TemplateView.as_view(template_name='commentaries/howto.html'), name='howto'),

    # Match a DOI-based link:
    url(r'^(?P<arxiv_or_DOI_string>10.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+)/$',
        views.commentary_detail, name='commentary'),
    # Match an arxiv-based link:
    # new style identifiers:
    url(r'^(?P<arxiv_or_DOI_string>arXiv:[0-9]{4,}.[0-9]{5,}(v[0-9]+)?)/$',
        views.commentary_detail, name='commentary'),
    # old style identifiers:
    url(r'^(?P<arxiv_or_DOI_string>arXiv:[a-z-]+/[0-9]{7,}(v[0-9]+)?)/$',
        views.commentary_detail, name='commentary'),

    url(r'^request_commentary$', views.request_commentary, name='request_commentary'),
    url(r'^request_commentary/published_article$', views.RequestPublishedArticle.as_view(),
        name='request_published_article'),
    url(r'^request_commentary/arxiv_preprint$', views.RequestArxivPreprint.as_view(),
        name='request_arxiv_preprint'),
    url(r'^prefill_using_DOI$', views.prefill_using_DOI, name='prefill_using_DOI'),
    url(r'^prefill_using_arxiv_identifier$', views.prefill_using_arxiv_identifier,
        name='prefill_using_arxiv_identifier'),
    url(r'^vet_commentary_requests$', views.vet_commentary_requests,
        name='vet_commentary_requests'),
    url(r'^vet_commentary_requests/(?P<commentary_id>[0-9]+)$', views.vet_commentary_requests,
        name='vet_commentary_requests_submit'),
    url(r'^vet_commentary_requests/(?P<commentary_id>[0-9]+)/modify$',
        views.modify_commentary_request, name='modify_commentary_request'),

    # Commentaries on SciPost Publications
    url(r'^publications/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/comment$',
        views.comment_on_publication, name='comment_on_publication')
]
