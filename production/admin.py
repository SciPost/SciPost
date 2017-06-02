from django.contrib import admin

from django import forms

from .models import ProductionStream, ProductionEvent

from submissions.models import Submission


class ProductionStreamAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))

    class Meta:
        model = ProductionStream
        fields = '__all__'

class ProductionStreamAdmin(admin.ModelAdmin):
    search_fields = ['submission']
    list_display = ['submission', 'opened', 'status']
    form = ProductionStreamAdminForm

admin.site.register(ProductionStream, ProductionStreamAdmin)


class ProductionEventAdminForm(forms.ModelForm):
    stream = forms.ModelChoiceField(
        queryset=ProductionStream.objects.order_by('-submission.arxiv_identifier_w_vn_nr'))

    class Meta:
        model = ProductionEvent
        fields = '__all__'

class ProductionEventAdmin(admin.ModelAdmin):
    search_field = ['stream', 'event', 'comment', 'noted_by']
    list_display = ['stream', 'event', 'noted_on', 'noted_by']
    form = ProductionEventAdminForm

admin.site.register(ProductionEvent, ProductionEventAdmin)
