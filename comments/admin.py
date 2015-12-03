from django.contrib import admin

from comments.models import *

admin.site.register(Comment)
admin.site.register(AuthorReply)
