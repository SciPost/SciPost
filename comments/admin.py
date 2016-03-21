from django.contrib import admin

from comments.models import *

class CommentAdmin(admin.ModelAdmin):
    search_fields = ['comment_text', 'author__user__last_name']

admin.site.register(Comment, CommentAdmin)


admin.site.register(AuthorReply)
