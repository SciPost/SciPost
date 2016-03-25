from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Comments
    url(r'^comment_submission_ack$', TemplateView.as_view(template_name='comments/comment_submission_ack.html'), name='comment_submission_ack'),
    url(r'^reply_to_comment/(?P<comment_id>[0-9]+)$', views.reply_to_comment, name='reply_to_comment'),
    url(r'^vet_submitted_comments$', views.vet_submitted_comments, name='vet_submitted_comments'),
    url(r'^vet_submitted_comment_ack/(?P<comment_id>[0-9]+)$', views.vet_submitted_comment_ack, name='vet_submitted_comment_ack'),
    url(r'^express_opinion/(?P<comment_id>[0-9]+)$', views.express_opinion, name='express_opinion'),
    url(r'^express_opinion/(?P<comment_id>[0-9]+)/(?P<opinion>[AND])$', views.express_opinion, name='express_opinion'),
]
