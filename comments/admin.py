from django.contrib import admin

from .constants import STATUS_VETTED
from .models import Comment


def comment_is_vetted(comment):
    '''Check if comment is vetted.'''
    return comment.status is STATUS_VETTED


class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_text', 'author', 'date_submitted', comment_is_vetted)
    date_hierarchy = 'date_submitted'
    list_filter = ('status',)
    comment_is_vetted.boolean = True


admin.site.register(Comment, CommentAdmin)
