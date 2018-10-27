__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Tag, Topic


class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(Tag, TagAdmin)


class TopicAdmin(admin.ModelAdmin):
    pass

admin.site.register(Topic, TopicAdmin)
