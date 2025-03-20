__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import Any
from django.contrib import admin
from django.core.handlers.asgi import HttpRequest
from django.db.models.fields.related import RelatedField
from django.db.models.query import QuerySet

from anonymization.models import (
    ContributorAnonymization,
    ProfileAnonymization,
    AnonymousContributor,
    AnonymousProfile,
)


@admin.register(AnonymousProfile)
class AnonymousProfileAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name"]
    search_fields = ["first_name", "last_name"]
    fields = ["first_name", "last_name"]

    def anonymization_status(self, obj):
        return obj.eponymization.status.value.title()


@admin.register(AnonymousContributor)
class AnonymousContributorAdmin(admin.ModelAdmin):
    list_display = ["profile__last_name", "profile__first_name"]
    fields = ["profile"]
    autocomplete_fields = ["profile"]
    search_fields = ["profile__first_name", "profile__last_name"]

    def profile__first_name(self, obj):
        return obj.profile.first_name

    def profile__last_name(self, obj):
        return obj.profile.last_name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("profile")

    def anonymization_status(self, obj):
        return obj.eponymization.status.value.title()

    # Override the profile field to use the AnonymousProfile model
    def get_field_queryset(
        self, db: None, db_field: RelatedField[Any, Any], request: HttpRequest | None
    ) -> QuerySet[Any] | None:
        if db_field.name == "profile":
            return AnonymousProfile.objects.all()
        return super().get_field_queryset(db, db_field, request)


@admin.register(ProfileAnonymization)
class ProfileAnonymizationAdmin(admin.ModelAdmin):
    list_display = ["uuid", "original", "anonymous", "status"]
    search_fields = ["uuid", "original__first_name", "original__last_name"]
    autocomplete_fields = ["original", "anonymous"]

    def status(self, obj):
        return obj.status.value.title()


@admin.register(ContributorAnonymization)
class ContributorAnonymizationAdmin(admin.ModelAdmin):
    list_display = ["uuid", "original", "anonymous", "status"]
    search_fields = [
        "uuid",
        "original__profile__first_name",
        "original__profile__last_name",
    ]
    autocomplete_fields = ["original", "anonymous"]

    def status(self, obj):
        return obj.status.value.title()
