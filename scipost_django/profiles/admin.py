__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from ethics.admin import RedFlagInline

from .models import Profile, ProfileEmail, ProfileNonDuplicates, Affiliation


class ProfileEmailInline(admin.TabularInline):
    model = ProfileEmail
    extra = 0


class AffiliationInline(admin.TabularInline):
    model = Affiliation
    extra = 0
    autocomplete_fields = [
        "organization",
    ]


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "email", "acad_field", "has_active_contributor"]
    search_fields = ["first_name", "last_name", "emails__email", "orcid_id"]
    inlines = [ProfileEmailInline, AffiliationInline, RedFlagInline]
    autocomplete_fields = ["topics"]


admin.site.register(Profile, ProfileAdmin)


class ProfileNonDuplicatesAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "profiles",
    ]


admin.site.register(ProfileNonDuplicates, ProfileNonDuplicatesAdmin)
