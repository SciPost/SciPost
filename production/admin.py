from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import ProductionStream, ProductionEvent, ProductionUser


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


admin.site.register(ProductionUser)
admin.site.register(ProductionStream, ProductionStreamAdmin)
