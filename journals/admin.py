from django.contrib import admin

from journals.models import Journal, Volume, Issue, Publication


class JournalAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(Journal, JournalAdmin)


class VolumeAdmin(admin.ModelAdmin):
    pass

admin.site.register(Volume, VolumeAdmin)


class IssueAdmin(admin.ModelAdmin):
    pass

admin.site.register(Issue, IssueAdmin)


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title', 'author_list']

admin.site.register(Publication, PublicationAdmin)
