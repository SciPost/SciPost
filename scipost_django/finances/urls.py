__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "finances"

urlpatterns = [
    path("", views.finances, name="finances"),
    path(
        "business_model/",
        TemplateView.as_view(template_name="finances/business_model.html"),
        name="business_model",
    ),
    path("apex", views.apex, name="apex"),
    path(
        "country_level_data",
        views.country_level_data,
        name="country_level_data",
    ),
    path(
        "_hx_country_level_data/<slug:country>",
        views._hx_country_level_data,
        name="_hx_country_level_data",
    ),
    # Subsidies
    path("subsidies/", views.SubsidyListView.as_view(), name="subsidies"),
    path("subsidies/add/", views.SubsidyCreateView.as_view(), name="subsidy_create"),
    path(
        "subsidies/<int:pk>/update/",
        views.SubsidyUpdateView.as_view(),
        name="subsidy_update",
    ),
    path(
        "subsidies/<int:pk>/delete/",
        views.SubsidyDeleteView.as_view(),
        name="subsidy_delete",
    ),
    path(
        "subsidies/<int:pk>/", views.SubsidyDetailView.as_view(), name="subsidy_details"
    ),
    path(
        "subsidies/<int:subsidy_id>/toggle_amount_visibility/",
        views.subsidy_toggle_amount_public_visibility,
        name="subsidy_toggle_amount_public_visibility",
    ),
    path(
        "subsidies/<int:subsidy_id>/attachments/add/",
        views.SubsidyAttachmentCreateView.as_view(),
        name="subsidyattachment_create",
    ),
    path(
        "subsidies/attachments/<int:pk>/update/",
        views.SubsidyAttachmentUpdateView.as_view(),
        name="subsidyattachment_update",
    ),
    path(
        "subsidies/attachments/<int:pk>/delete/",
        views.SubsidyAttachmentDeleteView.as_view(),
        name="subsidyattachment_delete",
    ),
    path(
        "subsidies/attachments/<int:attachment_id>/toggle_visibility/",
        views.subsidy_attachment_toggle_public_visibility,
        name="subsidy_attachment_toggle_public_visibility",
    ),
    path(
        "subsidies/<int:subsidy_id>/attachments/<int:attachment_id>",
        views.subsidy_attachment,
        name="subsidy_attachment",
    ),
    # Timesheets
    path("timesheets", views.timesheets, name="timesheets"),
    path("timesheets/detailed", views.timesheets_detailed, name="timesheets_detailed"),
    path("logs/<slug:slug>/delete", views.LogDeleteView.as_view(), name="log_delete"),
]
