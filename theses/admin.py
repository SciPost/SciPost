__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from django import forms

from theses.models import *

from scipost.models import Contributor


class ThesisLinkAdmin(admin.ModelAdmin):
    search_fields = ['requested_by__user__username', 'author', 'title']
    autocomplete_fields = [
        'requested_by',
        'vetted_by',
        'author_as_cont',
        'author_claims',
        'author_false_claims',
        'supervisor_as_cont',
    ]

admin.site.register(ThesisLink, ThesisLinkAdmin)
