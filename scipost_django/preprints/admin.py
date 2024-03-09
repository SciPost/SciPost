__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Preprint


@admin.register(Preprint)
class PreprintAdmin(admin.ModelAdmin):
    search_fields = [
        "identifier_w_vn_nr",
    ]


