__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Affiliation, Institution


admin.site.register(Affiliation)
admin.site.register(Institution)
