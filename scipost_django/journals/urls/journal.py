__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from journals import views as journals_views


app_name = 'urls.journals'

urlpatterns = [
    # Journal routes
    url(r'^issues$', journals_views.IssuesView.as_view(), name='issues'),
    url(r'^recent$', journals_views.redirect_to_about, name='recent'),
    url(r'^accepted$', journals_views.redirect_to_about, name='accepted'),
    url(r'^authoring$', journals_views.authoring, name='authoring'),
    url(r'^refereeing$', journals_views.refereeing, name='refereeing'),
    url(r'^about$', journals_views.about, name='about'),
    path(
        'metrics/<specialty:specialty>',
        journals_views.metrics,
        name='metrics'
    ),
    path(
        'metrics',
        journals_views.metrics,
        name='metrics'
    ),
]
