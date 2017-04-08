from django.contrib import admin

from commentaries.models import Commentary


class CommentaryAdmin(admin.ModelAdmin):
    search_fields = ['author_list', 'pub_abstract']
    list_display = ('__str__', 'vetted', 'latest_activity',)
    date_hierarchy = 'latest_activity'


admin.site.register(Commentary, CommentaryAdmin)
