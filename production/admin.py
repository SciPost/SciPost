from django.contrib import admin

from .models import ProductionStream, ProductionEvent


admin.site.register(ProductionStream)
admin.site.register(ProductionEvent)
