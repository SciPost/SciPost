__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import ProductionStream, ProductionEvent, ProductionUser, Proofs,\
    ProductionEventAttachment


def event_count(obj):
    return obj.events.count()


class ProductionUserInline(admin.StackedInline):
    model = ProductionUser
    extra = 0
    min_num = 0


class ProductionEventInline(admin.TabularInline):
    model = ProductionEvent
    extra = 1
    readonly_fields = ()


class ProductionStreamAdmin(GuardedModelAdmin):
    search_fields = ['submission']
    list_filter = ['status']
    list_display = ['submission', 'opened', 'status', event_count]
    inlines = (
        ProductionEventInline,
    )


class ProductionProofsAdmin(admin.ModelAdmin):
    list_display = ['stream', 'version', 'status', 'accessible_for_authors']
    list_filter = ['status', 'accessible_for_authors']


admin.site.register(Proofs, ProductionProofsAdmin)
admin.site.register(ProductionUser)
admin.site.register(ProductionEvent)
admin.site.register(ProductionEventAttachment)
admin.site.register(ProductionStream, ProductionStreamAdmin)
