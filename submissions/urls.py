from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Submissions
    url(r'^$', views.submissions, name='submissions'),
    url(r'^submission/(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^submit_manuscript$', views.submit_manuscript, name='submit_manuscript'),
    url(r'^submit_manuscript_ack$', views.submit_manuscript_ack, name='submit_manuscript_ack'),
    url(r'^process_new_submissions$', views.process_new_submissions, name='process_new_submissions'),
    url(r'^process_new_submission_ack/(?P<submission_id>[0-9]+)$', views.process_new_submission_ack, name='process_new_submission_ack'),
]
