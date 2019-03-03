__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Forum, Post


class ForumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name',]

admin.site.register(Forum, ForumAdmin)


class PostAdmin(admin.ModelAdmin):
    search_fields = ['posted_by', 'subject', 'text']

admin.site.register(Post, PostAdmin)
