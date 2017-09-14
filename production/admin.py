from django.contrib import admin

from .models import ProductionStream, ProductionEvent, ProductionUser


def event_count(obj):
    return obj.productionevent_set.count()


class ProductionUserInline(admin.StackedInline):
    model = ProductionUser
    extra = 0
    min_num = 0


class ProductionEventInline(admin.TabularInline):
    model = ProductionEvent
    extra = 1
    readonly_fields = ()


class ProductionStreamAdmin(admin.ModelAdmin):
    search_fields = ['submission']
    list_filter = ['status']
    list_display = ['submission', 'opened', 'status', event_count]
    inlines = (
        ProductionEventInline,
    )


admin.site.register(ProductionStream, ProductionStreamAdmin)
