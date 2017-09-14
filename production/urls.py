from django.conf.urls import url

from production import views as production_views

urlpatterns = [
    url(r'^$', production_views.production, name='production'),
    url(r'^completed$', production_views.completed, name='completed'),
    url(r'^officers/new$', production_views.user_to_officer, name='user_to_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/events/add$',
        production_views.add_event, name='add_event'),
    url(r'^streams/(?P<stream_id>[0-9]+)/officer/add$',
        production_views.add_officer, name='add_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/officer/(?P<officer_id>[0-9]+)/remove$',
        production_views.remove_officer, name='remove_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/mark_completed$',
        production_views.mark_as_completed, name='mark_as_completed'),
    url(r'^events/(?P<event_id>[0-9]+)/edit',
        production_views.UpdateEventView.as_view(), name='update_event'),
    url(r'^events/(?P<event_id>[0-9]+)/delete',
        production_views.DeleteEventView.as_view(), name='delete_event'),
]
