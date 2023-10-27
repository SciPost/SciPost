__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms import ChoiceField

from .models import CompetingInterest, RedFlag


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


class ConcerningObjectExistingFilter(admin.SimpleListFilter):
    title = "concerning object type"
    parameter_name = "concerning_object_type"

    def lookups(self, request, model_admin):
        return [
            (ct, ContentType.objects.get(id=ct).name.title())
            for ct in model_admin.model.objects.values_list(
                "concerning_object_type", flat=True
            ).distinct()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(concerning_object_type=self.value())
        else:
            return queryset


@admin.register(RedFlag)
class RedFlagAdmin(admin.ModelAdmin):
    search_fields = ("concerning_object_id", "raised_by__last_name")
    list_filter = ["resolved", ConcerningObjectExistingFilter]
    list_display = (
        "concerning_object",
        "raised_by",
        "description",
        "raised_on",
        "resolved",
    )
