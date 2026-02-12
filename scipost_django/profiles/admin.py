__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from ethics.admin import RedFlagInline

from .models import Profile, ProfileEmail, Affiliation


class ProfileEmailInline(admin.TabularInline):
    model = ProfileEmail
    autocomplete_fields = ["added_by"]
    exclude = ["verification_token", "token_expiration"]
    readonly_fields = ["domain"]
    extra = 0


class AffiliationInline(admin.TabularInline):
    model = Affiliation
    extra = 0
    autocomplete_fields = [
        "organization",
    ]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "email", "acad_field", "has_active_contributor"]
    search_fields = ["first_name", "last_name", "emails__email", "orcid_id"]
    inlines = [ProfileEmailInline, AffiliationInline, RedFlagInline]
    autocomplete_fields = ["topics"]
    readonly_fields = ["orcid_authenticated"]

    def get_queryset(self, request):
        return super().get_queryset(request).eponymous()

    # Set the orcid_authenticated field to false
    # if the orcid_id has been changed by the user
    def save_model(self, request, obj, form, change):
        if change:
            original_obj = Profile.objects.get(pk=obj.pk)
            if original_obj.orcid_id != obj.orcid_id:
                obj.orcid_authenticated = False
        obj.save()
