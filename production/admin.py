from django.contrib import admin

from django import forms

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


class ProductionEventAdminForm(forms.ModelForm):
    stream = forms.ModelChoiceField(
        queryset=ProductionStream.objects.order_by('-submission__arxiv_identifier_w_vn_nr'))

    class Meta:
        model = ProductionEvent
        fields = '__all__'


class ProductionEventAdmin(admin.ModelAdmin):
    search_field = ['stream', 'event', 'comment', 'noted_by']
    list_display = ['stream', 'event', 'noted_on', 'noted_by']
    form = ProductionEventAdminForm


admin.site.register(ProductionEvent, ProductionEventAdmin)
