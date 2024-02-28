__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import (
    ProductionStream,
    ProductionEvent,
    ProductionUser,
    Proofs,
    ProductionEventAttachment,
    ProofsRepository,
)

from django.utils.html import format_html


def event_count(obj):
    return obj.events.count()


@admin.register(ProductionUser)
class ProductionUserAdmin(admin.ModelAdmin):
    search_fields = [
        "user",
        "name",
    ]
    autocomplete_fields = [
        "user",
    ]




class ProductionUserInline(admin.StackedInline):
    model = ProductionUser
    extra = 0
    min_num = 0
    search_fields = [
        "user",
    ]
    autocomplete_fields = [
        "user",
    ]


class ProductionEventInline(admin.TabularInline):
    model = ProductionEvent
    extra = 1
    readonly_fields = ()
    search_fields = [
        "stream",
        "noted_by",
    ]
    autocomplete_fields = [
        "stream",
        "noted_by",
        "noted_to",
    ]


@admin.register(ProductionStream)
class ProductionStreamAdmin(GuardedModelAdmin):
    search_fields = [
        "submission__author_list",
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
    ]
    list_filter = ["status"]
    list_display = ["submission", "opened", "status", event_count]
    inlines = (ProductionEventInline,)
    autocomplete_fields = [
        "submission",
        "officer",
        "supervisor",
        "invitations_officer",
    ]




@admin.register(Proofs)
class ProductionProofsAdmin(admin.ModelAdmin):
    list_display = ["stream", "version", "status", "accessible_for_authors"]
    list_filter = ["status", "accessible_for_authors"]
    search_fields = [
        "stream",
    ]
    autocomplete_fields = [
        "stream",
        "uploaded_by",
    ]




admin.site.register(ProductionEventAttachment)


@admin.register(ProofsRepository)
class ProofsRepositoryAdmin(GuardedModelAdmin):
    search_fields = [
        "stream__submission__author_list",
        "stream__submission__title",
        "name",
    ]

    list_filter = ["status"]
    list_display = ["name", "status", "gitlab_link"]
    readonly_fields = ["stream", "template_paths", "gitlab_link"]

    def gitlab_link(self, obj):
        return format_html(
            '<a href="{1}" target="_blank">{0}</a>', obj.git_path, obj.git_url
        )

    def template_paths(self, obj):
        return format_html("<br>".join(obj.template_paths))


