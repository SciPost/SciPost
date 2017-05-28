from django.contrib import admin

from django import forms

from .models import VGM, Feedback, Nomination, Motion

from scipost.models import Contributor


class VGMAdmin(admin.ModelAdmin):
    search_fields = ['start_date']


admin.site.register(VGM, VGMAdmin)


class FeedbackAdmin(admin.ModelAdmin):
    search_fields = ['feedback', 'by']


admin.site.register(Feedback, FeedbackAdmin)


class NominationAdminForm(forms.ModelForm):
    in_agreement = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    in_notsure = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    in_disagreement = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))

    class Meta:
        model = Nomination
        fields = '__all__'

class NominationAdmin(admin.ModelAdmin):
    search_fields = ['last_name', 'first_name', 'by']
    form = NominationAdminForm

admin.site.register(Nomination, NominationAdmin)


class MotionAdminForm(forms.ModelForm):
    in_agreement = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    in_notsure = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    in_disagreement = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))

    class Meta:
        model = Motion
        fields = '__all__'

class MotionAdmin(admin.ModelAdmin):
    search_fields = ['background', 'motion', 'put_forward_by']
    form = MotionAdminForm

admin.site.register(Motion, MotionAdmin)
