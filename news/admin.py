from django.contrib import admin

from .models import NewsItem


class NewsItemAdmin(admin.ModelAdmin):
    search_fields = ['blurb', 'followup_link_text']
    list_display = ['__str__', 'on_homepage']


admin.site.register(NewsItem, NewsItemAdmin)
