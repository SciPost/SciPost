from django.conf.urls import url

from journals import views as journals_views

urlpatterns = [
    # Journal routes
    url(r'^issues$', journals_views.IssuesView.as_view(), name='issues'),
    url(r'^recent$', journals_views.RecentView.as_view(), name='recent'),
    url(r'^accepted$', journals_views.AcceptedView.as_view(), name='accepted'),
    url(r'^info_for_authors$', journals_views.info_for_authors, name='info_for_authors'),
    url(r'^about$', journals_views.about, name='about'),
]
