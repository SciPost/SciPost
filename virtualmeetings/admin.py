from django.contrib import admin

from .models import VGM, Feedback, Nomination, Motion


class VGMAdmin(admin.ModelAdmin):
    search_fields = ['start_date']


admin.site.register(VGM, VGMAdmin)


class FeedbackAdmin(admin.ModelAdmin):
    search_fields = ['feedback', 'by']


admin.site.register(Feedback, FeedbackAdmin)


class NominationAdmin(admin.ModelAdmin):
    search_fields = ['last_name', 'first_name', 'by']


admin.site.register(Nomination, NominationAdmin)


class MotionAdmin(admin.ModelAdmin):
    search_fields = ['background', 'motion', 'put_forward_by']


admin.site.register(Motion, MotionAdmin)
