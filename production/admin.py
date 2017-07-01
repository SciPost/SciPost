from django.contrib import admin

from .models import ProductionStream, ProductionEvent


def event_count(obj):
    return obj.productionevent_set.count()


class ProductionEventInline(admin.TabularInline):
    model = ProductionEvent
    extra = 1


class ProductionStreamAdmin(admin.ModelAdmin):
    search_fields = ['submission']
    list_filter = ['status']
    list_display = ['submission', 'opened', 'status', event_count]
    inlines = (
        ProductionEventInline,
    )


admin.site.register(ProductionStream, ProductionStreamAdmin)
