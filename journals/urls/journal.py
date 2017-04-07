from django.conf.urls import url

from journals import views as journals_views

urlpatterns = [
    # Journal routes
    # url(r'^$', journals_views.landing_page, name='landing_page'),
    url(r'^issues$', journals_views.issues, name='issues'),
    url(r'^recent$', journals_views.recent, name='recent'),
    url(r'^accepted$', journals_views.accepted, name='accepted'),
    url(r'^info_for_authors$', journals_views.info_for_authors, name='info_for_authors'),
    url(r'^about$', journals_views.about, name='about'),

]
