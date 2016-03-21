from django.contrib import admin

from theses.models import *


class ThesisLinkAdmin(admin.ModelAdmin):
    search_fields = ['requested_by__user__username', 'author', 'title']

admin.site.register(ThesisLink, ThesisLinkAdmin)


