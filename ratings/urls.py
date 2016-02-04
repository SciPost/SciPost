from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^vote_on_submission/(?P<submission_id>[0-9]+)$', views.vote_on_submission, name='vote_on_submission'),
    url(r'^vote_on_submission_ack$', views.vote_on_submission_ack, name='vote_on_submission_ack'),
    url(r'^vote_on_report/(?P<report_id>[0-9]+)$', views.vote_on_report, name='vote_on_report'),
    url(r'^vote_on_report_ack$', views.vote_on_report_ack, name='vote_on_report_ack'),
    url(r'^vote_on_commentary/(?P<commentary_id>[0-9]+)$', views.vote_on_commentary, name='vote_on_commentary'),
    url(r'^vote_on_commentary_ack$', views.vote_on_commentary_ack, name='vote_on_commentary_ack'),
    url(r'^vote_on_thesis/(?P<thesislink_id>[0-9]+)$', views.vote_on_thesis, name='vote_on_thesis'),
    url(r'^vote_on_thesis_ack$', views.vote_on_thesis_ack, name='vote_on_thesis_ack'),
    url(r'^vote_on_comment/(?P<comment_id>[0-9]+)$', views.vote_on_comment, name='vote_on_comment'),
    url(r'^vote_on_comment_ack$', views.vote_on_comment_ack, name='vote_on_comment_ack'),
    url(r'^vote_on_authorreply/(?P<authorreply_id>[0-9]+)$', views.vote_on_authorreply, name='vote_on_authorreply'),
    url(r'^vote_on_authorreply_ack$', views.vote_on_authorreply_ack, name='vote_on_authorreply_ack'),
]
