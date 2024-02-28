__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Petition, PetitionSignatory


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    search_fields = [
        "title",
        "headline",
        "preamble",
        "statement",
    ]
    autocomplete_fields = [
        "creator",
    ]




@admin.register(PetitionSignatory)
class PetitionSignatoryAdmin(admin.ModelAdmin):
    search_fields = ["last_name", "country", "institution"]
    autocomplete_fields = [
        "petition",
        "signatory",
        "organization",
    ]


