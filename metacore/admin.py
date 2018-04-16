from django.contrib import admin
from .services import get_crossref_test

# Register your models here.
def import_data_from_crossref(modeladmin, request, queryset):
    get_crossref_test()
