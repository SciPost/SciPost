from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.RegistrationInvitationsView.as_view(), name='list'),
    url(r'^pending_invitations$', views.PendingRegistrationInvitationsView.as_view(),
        name='list_pending_invitations'),
    url(r'^new$', views.RegistrationInvitationsCreateView.as_view(), name='new'),
    url(r'^(?P<pk>[0-9]+)$', views.RegistrationInvitationsUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete$', views.RegistrationInvitationsDeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>[0-9]+)/send_reminder$', views.RegistrationInvitationsReminderView.as_view(), name='send_reminder'),
    url(r'^cleanup$', views.cleanup, name='cleanup'),
]
