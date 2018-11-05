__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Profile, ProfileEmail, ProfileNonDuplicates


class ProfileEmailInline(admin.TabularInline):
    model = ProfileEmail
    extra = 0


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'emails__email', 'orcid_id']
    inlines = [ProfileEmailInline]

admin.site.register(Profile, ProfileAdmin)


admin.site.register(ProfileNonDuplicates)
