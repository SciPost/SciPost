from django.conf.urls import url

from . import views

urlpatterns = [
    # Comments
    url(r'^reports/(?P<report_id>[0-9]+)/reply$', views.reply_to_report, name='reply_to_report'),
    url(r'^vet_submitted$', views.vet_submitted_comments_list, name='vet_submitted_comments_list'),
    url(r'^new/(?P<type_of_object>[a-z]+)/(?P<object_id>[0-9]+)$', views.new_comment,
        name='new_comment'),
    url(r'^(?P<comment_id>[0-9]+)/reply$', views.reply_to_comment, name='reply_to_comment'),
    url(r'^(?P<comment_id>[0-9]+)/vet$', views.vet_submitted_comment,
        name='vet_submitted_comment'),
    url(r'^(?P<comment_id>[0-9]+)/express_opinion$', views.express_opinion,
        name='express_opinion'),
    url(r'^(?P<comment_id>[0-9]+)/express_opinion/(?P<opinion>[AND])$', views.express_opinion,
        name='express_opinion'),
]
