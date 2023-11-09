__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import Any, Optional
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import Field
from django.forms import ChoiceField, widgets
from django.forms.fields import TypedChoiceField
from django.http.request import HttpRequest
from blog import forms

from profiles.models import Profile

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
    model = RedFlag
    list_display = (
        "description",
        "raised_by",
        "raised_on",
        "resolved",
    )


class RedFlagInline(GenericTabularInline):
    ct_field = "concerning_object_type"
    ct_fk_field = "concerning_object_id"
    fk_name = "concerning_object"
    model = RedFlag
    extra = 0

    fields = ["raised_on", "raised_by", "description", "resolved"]
    autocomplete_fields = ["raised_by"]

    # modify the description textarea field to have 2 rows
    def formfield_for_dbfield(self, db_field: Field, **kwargs: Any) -> Any:
        if db_field.name == "description":
            kwargs["widget"] = widgets.Textarea(attrs={"rows": 1})
        return super().formfield_for_dbfield(db_field, **kwargs)

    # prefill the autocomplete field with the current user
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "raised_by":
            kwargs["initial"] = request.user.contributor
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
