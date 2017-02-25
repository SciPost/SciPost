from django.conf.urls import url

from . import views

urlpatterns = [
    # Comments
    url(r'^reply_to_comment/(?P<comment_id>[0-9]+)$', views.reply_to_comment, name='reply_to_comment'),
    url(r'^reply_to_report/(?P<report_id>[0-9]+)$', views.reply_to_report, name='reply_to_report'),
    url(r'^vet_submitted_comments$', views.vet_submitted_comments, name='vet_submitted_comments'),
    url(r'^vet_submitted_comment_ack/(?P<comment_id>[0-9]+)$', views.vet_submitted_comment_ack, name='vet_submitted_comment_ack'),
    url(r'^express_opinion/(?P<comment_id>[0-9]+)$', views.express_opinion, name='express_opinion'),
    url(r'^express_opinion/(?P<comment_id>[0-9]+)/(?P<opinion>[AND])$', views.express_opinion, name='express_opinion'),
    url(r'^new_comment/(?P<type_of_object>[a-z]+)/(?P<object_id>[0-9]+)$', views.new_comment, name='new_comment')
]
