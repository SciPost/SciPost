__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import ProductionStream, ProductionEvent, ProductionUser, Proofs,\
    ProductionEventAttachment


def event_count(obj):
    return obj.events.count()


class ProductionUserAdmin(admin.ModelAdmin):
    search_fields = [
        'user',
        'name',
    ]
    autocomplete_fields = [
        'user',
    ]

admin.site.register(ProductionUser, ProductionUserAdmin)


class ProductionUserInline(admin.StackedInline):
    model = ProductionUser
    extra = 0
    min_num = 0
    search_fields = [
        'user',
    ]
    autocomplete_fields = [
        'user',
    ]


class ProductionEventInline(admin.TabularInline):
    model = ProductionEvent
    extra = 1
    readonly_fields = ()
    search_fields = [
        'stream',
        'noted_by',
    ]
    autocomplete_fields = [
        'stream',
        'noted_by',
        'noted_to',
    ]


class ProductionStreamAdmin(GuardedModelAdmin):
    search_fields = ['submission__author_list', 'submission__title',
                     'submission__preprint__identifier_w_vn_nr']
    list_filter = ['status']
    list_display = ['submission', 'opened', 'status', event_count]
    inlines = (
        ProductionEventInline,
    )
    autocomplete_fields = [
        'submission',
        'officer',
        'supervisor',
        'invitations_officer',
    ]

admin.site.register(ProductionStream, ProductionStreamAdmin)


class ProductionProofsAdmin(admin.ModelAdmin):
    list_display = ['stream', 'version', 'status', 'accessible_for_authors']
    list_filter = ['status', 'accessible_for_authors']
    search_fields = [
        'stream',
    ]
    autocomplete_fields = [
        'stream',
        'uploaded_by',
    ]

admin.site.register(Proofs, ProductionProofsAdmin)


admin.site.register(ProductionEventAttachment)
