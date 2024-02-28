__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin


from .models import Webinar, WebinarRegistration


class WebinarRegistrationInline(admin.TabularInline):
    model = WebinarRegistration


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    inlines = [
        WebinarRegistrationInline,
    ]


