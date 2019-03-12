__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import Forum, Meeting, Post, Motion


class ForumAdmin(GuardedModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']

admin.site.register(Forum, ForumAdmin)


class MeetingAdmin(GuardedModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'preamble']

admin.site.register(Meeting, MeetingAdmin)


class PostAdmin(admin.ModelAdmin):
    search_fields = ['posted_by', 'subject', 'text']

admin.site.register(Post, PostAdmin)


class MotionAdmin(admin.ModelAdmin):
    search_fields = ['posted_by', 'subject', 'text']

admin.site.register(Motion, MotionAdmin)
