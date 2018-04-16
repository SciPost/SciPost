from django.contrib import admin
from .models import Citable, CitableWithDOI
from .services import get_crossref_test

# Register your models here.
# def import_data_from_crossref(modeladmin, request, queryset):
#     get_crossref_test()

# class CitableAdmin(admin.ModelAdmin):
#     # list_display = ['title', 'status']
#     # ordering = ['title']
#     actions = [import_data_from_crossref]

#     def get_queryset(self, request):
#         return []

# admin.site.register(Citable, CitableAdmin)
