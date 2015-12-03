from django.contrib import admin

from ratings.models import *

admin.site.register(CommentaryRating)
admin.site.register(CommentRating)
admin.site.register(SubmissionRating)
admin.site.register(ReportRating)
admin.site.register(AuthorReplyRating)

