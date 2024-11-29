__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from finances.admin import SubsidyInline

from .models import Funder, Grant, IndividualBudget


@admin.register(Funder)
class FunderAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "acronym",
        "identifier",
        "organization__name",
        "organization__acronym",
    ]
    autocomplete_fields = [
        "organization",
    ]


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    search_fields = [
        "funder__name",
        "number",
        "recipient_name",
        "recipient__user__last_name",
    ]
    autocomplete_fields = [
        "funder",
        "recipient",
    ]


@admin.register(IndividualBudget)
class IndividualBudgetAdmin(admin.ModelAdmin):
    search_fields = [
        "organization__name",
        "organization__acronym",
        "holder__first_name",
        "holder__last_name",
    ]
    autocomplete_fields = [
        "organization",
        "holder",
    ]
    inlines = [
        SubsidyInline,
    ]
