from django.contrib import admin

from commentaries.models import *


class CommentaryAdmin(admin.ModelAdmin):
    search_fields = ['author_list', 'pub_abstract']

admin.site.register(Commentary, CommentaryAdmin)


