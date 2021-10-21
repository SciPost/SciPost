__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views

app_name = 'commentaries'

urlpatterns = [
    # Commentaries
    path(
        '',
        views.CommentaryListView.as_view(),
        name='commentaries'
    ),
    path(
        'howto',
        TemplateView.as_view(template_name='commentaries/howto.html'),
        name='howto'
    ),

    # Match a DOI-based link:
    re_path(
        r'^(?P<arxiv_or_DOI_string>10.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+)/$',
        views.commentary_detail,
        name='commentary'
    ),
    # Match an arxiv-based link:
    # new style identifiers:
    re_path(
        r'^(?P<arxiv_or_DOI_string>arXiv:[0-9]{4,}.[0-9]{5,}(v[0-9]+)?)/$',
        views.commentary_detail,
        name='commentary'
    ),
    # old style identifiers:
    re_path(
        r'^(?P<arxiv_or_DOI_string>arXiv:[a-z-]+/[0-9]{7,}(v[0-9]+)?)/$',
        views.commentary_detail,
        name='commentary'
    ),

    path(
        'request_commentary',
        views.request_commentary,
        name='request_commentary'
    ),
    path(
        'request_commentary/published_article',
        views.RequestPublishedArticle.as_view(),
        name='request_published_article'
    ),
    path(
        'request_commentary/arxiv_preprint',
        views.RequestArxivPreprint.as_view(),
        name='request_arxiv_preprint'
    ),
    path(
        'prefill_using_DOI',
        views.prefill_using_DOI,
        name='prefill_using_DOI'
    ),
    path(
        'prefill_using_arxiv_identifier',
        views.prefill_using_arxiv_identifier,
        name='prefill_using_arxiv_identifier'
    ),
    path(
        'vet_commentary_requests',
        views.vet_commentary_requests,
        name='vet_commentary_requests'
    ),
    path(
        'vet_commentary_requests/<int:commentary_id>',
        views.vet_commentary_requests,
        name='vet_commentary_requests_submit'
    ),
    path(
        'vet_commentary_requests/<int:commentary_id>/modify',
        views.modify_commentary_request,
        name='modify_commentary_request'
    ),

    # Commentaries on SciPost Publications
    re_path(
        r'^publications/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/comment$',
        views.comment_on_publication,
        name='comment_on_publication'
    )
]
