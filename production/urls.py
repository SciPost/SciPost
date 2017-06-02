from django.conf.urls import url

from production import views as production_views

urlpatterns = [
    url(r'^$', production_views.production, name='production'),
    url(r'^completed$', production_views.completed, name='completed'),
    url(r'^add_event/(?P<stream_id>[0-9]+)$',
        production_views.add_event, name='add_event'),
    url(r'^mark_as_completed/(?P<stream_id>[0-9]+)$',
        production_views.mark_as_completed, name='mark_as_completed'),
]
