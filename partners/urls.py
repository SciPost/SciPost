from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.supporting_partners, name='partners'),
    url(r'^petition/(?P<slug>[-\w]+)/sign$', views.sign_petition, name='sign_petition'),
    url(r'^petition/(?P<slug>[-\w]+)$', views.petition, name='petition'),
    url(r'^dashboard$', views.dashboard, name='dashboard'),
    url(r'^membership_request$', views.membership_request, name='membership_request'),
    url(r'^process_contact_requests$', views.process_contact_requests, name='process_contact_requests'),

    # Prospects
    url(r'^prospects/add$', views.add_prospective_partner,
        name='add_prospective_partner'),
    url(r'^prospects/contacts/(?P<contact_id>[0-9]+)/email$',
        views.email_prospartner_contact, name='email_prospartner_contact'),

    url(r'^prospects/(?P<prospartner_id>[0-9]+)/contacts/add$',
        views.add_prospartner_contact, name='add_prospartner_contact'),
    url(r'^prospects/(?P<prospartner_id>[0-9]+)/promote$',
        views.promote_prospartner, name='promote_prospartner'),
    url(r'^prospects/(?P<prospartner_id>[0-9]+)/email_generic',
        views.email_prospartner_generic, name='email_prospartner_generic'),
    url(r'^prospects/(?P<prospartner_id>[0-9]+)/events/add$',
        views.add_prospartner_event, name='add_prospartner_event'),

    # Agreements
    url(r'agreements/new$', views.add_agreement, name='add_agreement'),
    url(r'agreements/(?P<agreement_id>[0-9]+)$', views.agreement_details,
        name='agreement_details'),
    url(r'agreements/(?P<agreement_id>[0-9]+)/attachments/(?P<attachment_id>[0-9]+)$',
        views.agreement_attachments, name='agreement_attachments'),

    # Institutions
    url(r'institutions/(?P<institution_id>[0-9]+)/edit$', views.institution_edit,
        name='institution_edit'),

    # Users
    url(r'activate/(?P<activation_key>.+)$', views.activate_account, name='activate_account'),

    # Partners
    url(r'(?P<partner_id>[0-9]+)$', views.partner_view, name='partner_view'),
    url(r'(?P<partner_id>[0-9]+)/edit$', views.partner_edit, name='partner_edit'),
    url(r'(?P<partner_id>[0-9]+)/contacts/add$', views.partner_add_contact,
        name='partner_add_contact'),
    url(r'(?P<partner_id>[0-9]+)/contacts/request$', views.partner_request_contact,
        name='partner_request_contact'),
]
