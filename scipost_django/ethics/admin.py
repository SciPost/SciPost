__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import Field
from django.forms import widgets
from django.utils.safestring import mark_safe

from preprints.servers.server import PreprintServer

from .models import (
    CoauthoredWork,
    Coauthorship,
    CompetingInterest,
    GenAIDisclosure,
    RedFlag,
)

from typing import Any


class CoauthorshipInline(admin.TabularInline[Coauthorship]):
    model = Coauthorship
    extra = 0
    fields = ("profile", "coauthor", "work", "status", "verified_by", "created")
    readonly_fields = ("created", "modified")
    autocomplete_fields = ("profile", "coauthor", "work", "verified_by")


@admin.register(CompetingInterest)
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
    inlines = [CoauthorshipInline]


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


@admin.register(GenAIDisclosure)
class GenAIDisclosureAdmin(admin.ModelAdmin):
    model = GenAIDisclosure
    list_display = ("for_object", "was_used", "contributor", "use_details")
    search_fields = (
        "contributor__profile__last_name",
        "contributor__profile__first_name",
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
        "publication__title",
        "publication__accepted_submission__preprint__identifier_w_vn_nr",
    )
    autocomplete_fields = ("contributor",)


class GenAIDisclosureInline(GenericTabularInline):
    ct_field = "content_type"
    ct_fk_field = "object_id"
    fk_name = "for_object"
    model = GenAIDisclosure
    extra = 0

    fields = ["was_used", "use_details", "contributor"]
    autocomplete_fields = ["contributor"]

    # prefill the autocomplete field with the current user
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "contributor":
            kwargs["initial"] = request.user.contributor
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_dbfield(self, db_field: Field, **kwargs: Any) -> Any:
        if db_field.name == "use_details":
            kwargs["widget"] = widgets.Textarea(attrs={"rows": 2})
        return super().formfield_for_dbfield(db_field, **kwargs)


@admin.register(Coauthorship)
class CoauthorshipAdmin(admin.ModelAdmin[Coauthorship]):
    model = Coauthorship
    list_display = ("profile", "coauthor", "work_title_with_url", "status")
    search_fields = (
        "profile__last_name",
        "coauthor__last_name",
        "work__title",
        "work__doi",
        "work__identifier",
    )
    autocomplete_fields = (
        "profile",
        "coauthor",
        "verified_by",
        "work",
        "competing_interest",
    )
    readonly_fields = ("created", "modified")
    list_filter = ("status",)

    def work_title_with_url(self, obj: Coauthorship):
        if obj.work:
            return mark_safe(
                f'<a href="{obj.work.url}" target="_blank" rel="noopener">{obj.work.title}</a>'
            )
        return ""


@admin.register(CoauthoredWork)
class CoauthoredWorkAdmin(admin.ModelAdmin[CoauthoredWork]):
    model = CoauthoredWork
    list_display = (
        "server_source",
        "identifier_or_doi",
        "title",
        "authors_str",
    )
    list_filter = ("server_source",)
    search_fields = ("title", "identifier", "doi")

    def identifier_or_doi(self, obj: CoauthoredWork):
        return obj.identifier or obj.doi

    def formfield_for_dbfield(self, db_field: Field, **kwargs: Any) -> Any:
        if db_field.name == "server_source":
            kwargs["widget"] = widgets.Select(
                choices=[("", "-" * 9)]
                + [
                    (server.value, server.name.title())
                    for server in PreprintServer.__members__.values()
                ]
            )
        return super().formfield_for_dbfield(db_field, **kwargs)
