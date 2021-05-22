__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'forums'

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
        r'^meeting/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/$',
        views.MeetingCreateView.as_view(),
        name='meeting_create'
    ),
    url(
        r'^meeting/add/$',
        views.MeetingCreateView.as_view(),
        name='meeting_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/$',
        views.ForumDetailView.as_view(),
        name='forum_detail'
    ),
    url(
        r'^(?P<slug>[\w-]+)/update/$',
        views.ForumUpdateView.as_view(),
        name='forum_update'
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
        r'^(?P<slug>[\w-]+)/post/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/$',
        views.PostCreateView.as_view(),
        name='post_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/motion/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/$',
        views.MotionCreateView.as_view(),
        name='motion_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/post/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/confirm/$',
        views.PostConfirmCreateView.as_view(),
        name='post_confirm_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/motion/(?P<parent_model>[a-z]+)/(?P<parent_id>[0-9]+)/add/confirm/$',
        views.MotionConfirmCreateView.as_view(),
        name='motion_confirm_create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/motion/(?P<motion_id>[0-9]+)/(?P<vote>[YMNA])/$',
        views.motion_vote,
        name='motion_vote'
    ),
]
