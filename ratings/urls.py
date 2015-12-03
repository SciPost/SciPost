from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^vote_on_submission/(?P<submission_id>[0-9]+)$', views.vote_on_submission, name='vote_on_submission'),
    url(r'^vote_on_submission_ack$', views.vote_on_submission_ack, name='vote_on_submission_ack'),
    url(r'^vote_on_report/(?P<report_id>[0-9]+)$', views.vote_on_report, name='vote_on_report'),
    url(r'^vote_on_report_ack$', views.vote_on_report_ack, name='vote_on_report_ack'),
    url(r'^vote_on_commentary/(?P<commentary_id>[0-9]+)$', views.vote_on_commentary, name='vote_on_commentary'),
    url(r'^vote_on_commentary_ack$', views.vote_on_commentary_ack, name='vote_on_commentary_ack'),
    url(r'^vote_on_comment/(?P<comment_id>[0-9]+)$', views.vote_on_comment, name='vote_on_comment'),
    url(r'^vote_on_comment_ack$', views.vote_on_comment_ack, name='vote_on_comment_ack'),
]
