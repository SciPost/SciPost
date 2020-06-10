__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Tag, Topic, RelationAsym, RelationSym


class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(Tag, TagAdmin)


class TopicAdmin(admin.ModelAdmin):
    search_fields = [
        'name'
    ]

admin.site.register(Topic, TopicAdmin)


admin.site.register(RelationAsym)
admin.site.register(RelationSym)
