__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .constants import STATUS_VETTED
from .models import Comment


def comment_opening(comment):
    return comment.comment_text[:30] + '...'


def comment_is_vetted(comment):
    '''Check if comment is vetted.'''
    return comment.status is STATUS_VETTED


def comment_is_anonymous(comment):
    '''Check if comment is vetted.'''
    return comment.anonymous


class CommentAdmin(GuardedModelAdmin):
    list_display = (
        comment_opening, 'author', 'date_submitted', comment_is_vetted, comment_is_anonymous)
    date_hierarchy = 'date_submitted'
    list_filter = ('status',)
    comment_is_vetted.boolean = True
    comment_is_anonymous.boolean = True
    raw_id_fields = [
        'vetted_by',
        'author',
    ]

admin.site.register(Comment, CommentAdmin)
