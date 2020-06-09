__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from django import forms

from commentaries.models import Commentary

from scipost.models import Contributor


class CommentaryAdminForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().select_related('user'))
    authors_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().select_related('user'))
    authors_false_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().select_related('user'))

    class Meta:
        model = Commentary
        fields = '__all__'


class CommentaryAdmin(admin.ModelAdmin):
    search_fields = ['author_list', 'pub_abstract']
    list_display = ('__str__', 'vetted', 'latest_activity',)
    date_hierarchy = 'latest_activity'
    form = CommentaryAdminForm
    raw_id_fields = [
        'requested_by',
        'vetted_by',
        'scipost_publication',
    ]

admin.site.register(Commentary, CommentaryAdmin)
