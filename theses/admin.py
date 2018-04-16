__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from django import forms

from theses.models import *

from scipost.models import Contributor


class ThesisLinkAdminForm(forms.ModelForm):
    author_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    author_false_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    supervisor_as_cont = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))

    class Meta:
        model = ThesisLink
        fields = '__all__'

class ThesisLinkAdmin(admin.ModelAdmin):
    search_fields = ['requested_by__user__username', 'author', 'title']
    form = ThesisLinkAdminForm

admin.site.register(ThesisLink, ThesisLinkAdmin)
