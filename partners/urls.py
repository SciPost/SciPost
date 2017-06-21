from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.supporting_partners, name='partners'),
    url(r'^dashboard$', views.dashboard, name='dashboard'),
    url(r'^membership_request$', views.membership_request, name='membership_request'),
    url(r'^manage$', views.manage, name='manage'),
    url(r'^prospect_partners/add$', views.add_prospective_partner,
        name='add_prospective_partner'),
    url(r'^prospect_partners/contacts/(?P<contact_id>[0-9]+)/email$',
        views.email_prospartner_contact, name='email_prospartner_contact'),
    url(r'^prospect_partner/(?P<prospartner_id>[0-9]+)/contacts/add$',
        views.add_prospartner_contact, name='add_prospartner_contact'),
    url(r'^prospect_partner/(?P<prospartner_id>[0-9]+)/promote$',
        views.promote_prospartner, name='promote_prospartner'),
    url(r'^prospect_partner/(?P<prospartner_id>[0-9]+)/events/add$',
        views.add_prospartner_event, name='add_prospartner_event'),
]
