__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from django import forms
from django.core.handlers.asgi import HttpRequest
from django.db.models.query import QuerySet

from theses.models import *

from scipost.models import Contributor


@admin.register(ThesisLink)
class ThesisLinkAdmin(admin.ModelAdmin):
    search_fields = ["requested_by__dbuser__username", "author", "title"]
    autocomplete_fields = [
        "requested_by",
        "vetted_by",
        "author_as_cont",
        "author_claims",
        "author_false_claims",
        "supervisor_as_cont",
    ]
    list_display = [
        "requested_by__profile",
        "title",
        "vetted",
        "latest_activity",
    ]
    list_filter = [
        "vetted",
        "type",
        "acad_field",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("requested_by__profile")
