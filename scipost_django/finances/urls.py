__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
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
    path(
        "subsidies/",
        include(
            [
                path(
                    "_hx_subsidy_list",
                    views._hx_subsidy_list,
                    name="_hx_subsidy_list",
                ),
                path(
                    "<int:subsidy_id>/",
                    include(
                        [
                            path(
                                "_hx_subsidy_finadmin_details",
                                views._hx_subsidy_finadmin_details,
                                name="_hx_subsidy_finadmin_details",
                            ),
                            path(
                                "payment/",
                                include(
                                    [
                                        path(
                                            "button",
                                            views._hx_subsidypayment_button,
                                            name="_hx_subsidypayment_button",
                                        ),
                                        path(
                                            "form",
                                            views._hx_subsidypayment_form,
                                            name="_hx_subsidypayment_form",
                                        ),
                                        path(
                                            "<int:subsidypayment_id>",
                                            include(
                                                [
                                                    path(
                                                        "",
                                                        views._hx_subsidypayment_form,
                                                        name="_hx_subsidypayment_form",
                                                    ),
                                                    path(
                                                        "delete",
                                                        views._hx_subsidypayment_delete,
                                                        name="_hx_subsidypayment_delete",
                                                    ),
                                                ]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path("subsidies/", views.subsidy_list, name="subsidies"),
    path(
        "subsidies/old", views.SubsidyListView.as_view(), name="subsidies_old"
    ),  # deprecated
    path("subsidies/add/", views.SubsidyCreateView.as_view(), name="subsidy_create"),
    path(
        "subsidies/add/sponsorship_from_organization/<int:organization_id>",
        views.OrganizationSponsorshipSubsidyCreateView.as_view(),
        name="subsidy_sponsorship_create",
    ),
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
        "subsidies/autocomplete/",
        views.SubsidyAutocompleteView.as_view(),
        name="subsidy_autocomplete",
    ),
    path(
        "subsidies/_hx_dynsel_/page",
        views.HXDynselSubsidyResultPage.as_view(),
        name="_hx_dynsel_subsidy_result_page",
    ),
    path(
        "subsidies/_hx_dynsel/select_option",
        views.HXDynselSubsidySelectOption.as_view(),
        name="_hx_dynsel_subsidy_select_option",
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
        "subsidies/attachments/add/",
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
        "subsidies/attachments/<int:attachment_id>",
        views.subsidy_attachment,
        name="subsidy_attachment",
    ),
    path(
        "subsidies/attachments/orphaned/",
        views.subsidyattachment_orphaned_list,
        name="subsidyattachment_orphaned_list",
    ),
    path(
        "subsidies/attachments/orphaned/_hx_list_page",
        views._hx_subsidyattachment_list_page,
        name="_hx_subsidyattachment_list_page",
    ),
    path(
        "subsidies/attachments/_hx_link_form/<int:attachment_id>",
        views._hx_subsidyattachment_link_form,
        name="_hx_subsidyattachment_link_form",
    ),
    # Timesheets
    path("timesheets", views.timesheets, name="timesheets"),
    path("timesheets/detailed", views.timesheets_detailed, name="timesheets_detailed"),
    path("timesheets/mine", views.personal_timesheet, name="personal_timesheet"),
    path("logs/<slug:slug>/delete", views._hx_worklog_delete, name="log_delete"),
    # PeriodicReports
    path(
        "periodicreport/<int:pk>/file",
        views.periodicreport_file,
        name="periodicreport_file",
    ),
]
