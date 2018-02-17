from django.contrib import admin

from .models import RegistrationInvitation


class RegistrationInvitationAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_sent_first'
    search_fields = ['first_name', 'last_name', 'email', 'invitation_key']
    list_display = ['__str__', 'invitation_type', 'invited_by', 'status']
    list_filter = ['invitation_type', 'message_style', 'status']


admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)
