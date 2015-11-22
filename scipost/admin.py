from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from scipost.models import Contributor, Commentary, CommentaryRating, Comment, CommentRating, Submission, SubmissionRating, Report, ReportRating, AuthorReply, AuthorReplyRating

#class ContributorInline(admin.StackedInline):
#    model = Contributor

#class UserAdmin(UserAdmin):
#    inlines = (ContributorInline, )

#admin.site.unregister(User)
#admin.site.register(User, UserAdmin)

admin.site.register(Contributor)
admin.site.register(Commentary)
admin.site.register(CommentaryRating)
admin.site.register(Comment)
admin.site.register(CommentRating)
admin.site.register(Submission)
admin.site.register(SubmissionRating)
admin.site.register(Report)
admin.site.register(ReportRating)
admin.site.register(AuthorReply)
admin.site.register(AuthorReplyRating)
