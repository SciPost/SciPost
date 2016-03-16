from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Comments
    url(r'^comment_submission_ack$', TemplateView.as_view(template_name='comments/comment_submission_ack.html'), name='comment_submission_ack'),
    url(r'^reply_to_comment/(?P<comment_id>[0-9]+)$', views.reply_to_comment, name='reply_to_comment'),
    url(r'^vet_submitted_comments$', views.vet_submitted_comments, name='vet_submitted_comments'),
    url(r'^vet_submitted_comment_ack/(?P<comment_id>[0-9]+)$', views.vet_submitted_comment_ack, name='vet_submitted_comment_ack'),
    url(r'^author_reply_to_comment/(?P<comment_id>[0-9]+)$', views.author_reply_to_comment, name='author_reply_to_comment'),
    url(r'^author_reply_to_report/(?P<report_id>[0-9]+)$', views.author_reply_to_report, name='author_reply_to_report'),
    url(r'^vet_author_replies$', views.vet_author_replies, name='vet_author_replies'),
    url(r'^vet_author_reply_ack/(?P<reply_id>[0-9]+)$', views.vet_author_reply_ack, name='vet_author_reply_ack'),
]
