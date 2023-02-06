__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import CompetingInterest


class CompetingInterestAdmin(admin.ModelAdmin):
    search_fields = (
        "profile__last_name",
        "related_profile__last_name",
        "affected_submissions__title",
        "affected_submissions__preprint__identifier_w_vn_nr",
        "affected_publications__title",
        "affected_publications__doi_label",
    )
    list_filter = ("nature",)
    list_display = (
        "nature",
        "profile",
        "related_profile",
        "date_from",
        "date_until",
    )
    autocomplete_fields = (
        "profile",
        "related_profile",
        "declared_by",
        "affected_submissions",
        "affected_publications",
    )


admin.site.register(CompetingInterest, CompetingInterestAdmin)
