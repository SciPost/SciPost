__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from django import forms

from commentaries.models import Commentary

from scipost.models import Contributor


@admin.register(Commentary)
class CommentaryAdmin(admin.ModelAdmin):
    search_fields = ["author_list", "pub_abstract"]
    list_display = (
        "__str__",
        "vetted",
        "latest_activity",
    )
    date_hierarchy = "latest_activity"
    autocomplete_fields = [
        "requested_by",
        "vetted_by",
        "scipost_publication",
        "authors",
        "authors_claims",
        "authors_false_claims",
    ]


