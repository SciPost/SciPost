__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'orcid_id']

admin.site.register(Profile, ProfileAdmin)
