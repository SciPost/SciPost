__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.HelpdeskView.as_view(),
        name='helpdesk'
    ),
    url(
        r'^queue/add/$',
        views.QueueCreateView.as_view(),
        name='queue_create'
    ),
    url(
        r'^queue/(?P<slug>[\w-]+)/$',
        views.QueueDetailView.as_view(),
        name='queue_detail'
    ),
]
