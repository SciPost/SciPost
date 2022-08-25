__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path(
        "organization-autocomplete",
        views.OrganizationAutocompleteView.as_view(),
        name="organization-autocomplete",
    ),
    path("", views.OrganizationListView.as_view(), name="organizations"),
    path("add/", views.OrganizationRorListView.as_view(), name="organization_ror"),
    path("add/", views.OrganizationCreateView.as_view(), name="organization_create"),
    path(
        "<int:pk>/update/",
        views.OrganizationUpdateView.as_view(),
        name="organization_update",
    ),
    path(
        "<int:pk>/delete/",
        views.OrganizationDeleteView.as_view(),
        name="organization_delete",
    ),
    path(
        "<int:pk>/", views.OrganizationDetailView.as_view(), name="organization_detail"
    ),
    path(
        "get_organization_detail",
        views.get_organization_detail,
        name="get_organization_detail",
    ),
    path(
        "<int:pk>/orgevent/add/",
        views.OrganizationEventCreateView.as_view(),
        name="organizationevent_create",
    ),
    path(
        "organizationevents/",
        views.OrganizationEventListView.as_view(),
        name="organizationevent_list",
    ),
    path(
        "add_contactperson/<organization_id>/",
        views.ContactPersonCreateView.as_view(),
        name="contactperson_create",
    ),
    path(
        "contactperson/add/",
        views.ContactPersonCreateView.as_view(),
        name="contactperson_create",
    ),
    path(
        "contactperson/<int:pk>/update/",
        views.ContactPersonUpdateView.as_view(),
        name="contactperson_update",
    ),
    path(
        "contactperson/<int:pk>/delete/",
        views.ContactPersonDeleteView.as_view(),
        name="contactperson_delete",
    ),
    path(
        "contactpersons/",
        views.ContactPersonListView.as_view(),
        name="contactperson_list",
    ),
    path(
        "contactperson/<int:contactperson_id>/email/<str:mail>",
        views.email_contactperson,
        name="email_contactperson",
    ),
    path(
        "contactperson/<int:contactperson_id>/email/",
        views.email_contactperson,
        name="email_contactperson",
    ),
    path(
        # For upgrading a ContactPerson to a Contact
        "add_contact/<int:organization_id>/<int:contactperson_id>/",
        views.organization_add_contact,
        name="add_contact",
    ),
    path(
        "add_contact/<int:organization_id>/",
        views.organization_add_contact,
        name="add_contact",
    ),
    path(
        "activate/<str:activation_key>", views.activate_account, name="activate_account"
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "contact/<int:pk>/", views.ContactDetailView.as_view(), name="contact_details"
    ),
    path(
        "contactrole/<int:pk>/update/",
        views.ContactRoleUpdateView.as_view(),
        name="contactrole_update",
    ),
    path(
        "contactrole/<int:pk>/delete/",
        views.ContactRoleDeleteView.as_view(),
        name="contactrole_delete",
    ),
    path(
        "contactrole/<contactrole_id>/email/<str:mail>",
        views.email_contactrole,
        name="email_contactrole",
    ),
    path(
        "contactrole/<contactrole_id>/email/",
        views.email_contactrole,
        name="email_contactrole",
    ),
]
