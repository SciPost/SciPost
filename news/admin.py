__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import NewsLetter, NewsItem, NewsLetterNewsItemsTable


class NewsLetterNewsItemsTableInline(admin.TabularInline):
    model = NewsLetterNewsItemsTable

class NewsLetterAdmin(admin.ModelAdmin):
    search_fields = ['intro', 'closing']
    list_display = ['__str__', 'published']
    inlines = [NewsLetterNewsItemsTableInline]

admin.site.register(NewsLetter, NewsLetterAdmin)


class NewsItemAdmin(admin.ModelAdmin):
    search_fields = ['blurb', 'followup_link_text']
    list_display = ['__str__', 'published', 'on_homepage']


admin.site.register(NewsItem, NewsItemAdmin)
