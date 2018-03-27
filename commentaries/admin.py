from django.contrib import admin

from django import forms

from commentaries.models import Commentary

from scipost.models import Contributor


class CommentaryAdminForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    authors_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    authors_false_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))

    class Meta:
        model = Commentary
        fields = '__all__'


class CommentaryAdmin(admin.ModelAdmin):
    search_fields = ['author_list', 'pub_abstract']
    list_display = ('__str__', 'vetted', 'latest_activity',)
    date_hierarchy = 'latest_activity'
    form = CommentaryAdminForm


admin.site.register(Commentary, CommentaryAdmin)
