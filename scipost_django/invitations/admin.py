__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import RegistrationInvitation, CitationNotification


class RegistrationInvitationAdmin(admin.ModelAdmin):
    date_hierarchy = "date_sent_first"
    search_fields = ["first_name", "last_name", "email", "invitation_key"]
    list_display = ["__str__", "invitation_type", "invited_by", "status"]
    list_filter = ["invitation_type", "message_style", "status"]
    autocomplete_fields = [
        "profile",
        "invited_by",
        "created_by",
    ]


admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)


class CitationNotificationAdmin(admin.ModelAdmin):
    date_hierarchy = "date_sent"
    search_fields = [
        "invitation__first_name",
        "invitation__last_name",
        "contributor__user__first_name",
        "contributor__user__last_name",
    ]
    list_display = ["__str__", "created_by", "date_sent", "processed"]
    list_filter = ["processed"]
    autocomplete_fields = [
        "invitation",
        "contributor",
        "submission",
        "publication",
        "created_by",
    ]


admin.site.register(CitationNotification, CitationNotificationAdmin)
