__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from journals import views as journals_views

urlpatterns = [
    # Journal routes
    url(r'^issues$', journals_views.IssuesView.as_view(), name='issues'),
    url(r'^recent$', journals_views.redirect_to_about, name='recent'),
    url(r'^accepted$', journals_views.redirect_to_about, name='accepted'),
    url(r'^info_for_authors$', journals_views.info_for_authors, name='info_for_authors'),
    url(r'^about$', journals_views.about, name='about'),
]
