from django.contrib import admin

from comments.models import Comment


class CommentAdmin(admin.ModelAdmin):
    search_fields = ['comment_text', 'author__user__last_name']


admin.site.register(Comment, CommentAdmin)
