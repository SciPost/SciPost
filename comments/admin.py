from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .constants import STATUS_VETTED
from .models import Comment


def comment_opening(comment):
    return comment.comment_text[:30] + '...'


def comment_is_vetted(comment):
    '''Check if comment is vetted.'''
    return comment.status is STATUS_VETTED


class CommentAdmin(GuardedModelAdmin):
    list_display = (comment_opening, 'author', 'date_submitted', comment_is_vetted)
    date_hierarchy = 'date_submitted'
    list_filter = ('status', 'content_type',)
    comment_is_vetted.boolean = True


admin.site.register(Comment, CommentAdmin)
