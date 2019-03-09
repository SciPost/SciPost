__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^forum/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/$',
        views.ForumCreateView.as_view(),
        name='forum_create'
    ),
    url(
        r'^add/$',
        views.ForumCreateView.as_view(),
        name='forum_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/$',
        views.ForumDetailView.as_view(),
        name='forum_detail'
    ),
    url(
        r'^(?P<slug>[\w-]+)/delete/$',
        views.ForumDeleteView.as_view(),
        name='forum_delete'
    ),
    url(
        r'^(?P<slug>[\w-]+)/permissions/(?P<group_id>[0-9]+)/$',
        views.ForumPermissionsView.as_view(),
        name='forum_permissions'
    ),
    url(
        r'^(?P<slug>[\w-]+)/permissions/$',
        views.ForumPermissionsView.as_view(),
        name='forum_permissions'
    ),
    url(
        r'^$',
        views.ForumListView.as_view(),
        name='forums'
    ),
    url(
        r'(?P<slug>[\w-]+)/post/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/$',
        views.PostCreateView.as_view(),
        name='post_create'
    ),
    url(
        r'(?P<slug>[\w-]+)/post/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/confirm/$',
        views.PostConfirmCreateView.as_view(),
        name='post_confirm_create'
    ),
]
