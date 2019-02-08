__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Subsidy, WorkLog


admin.site.register(Subsidy)

admin.site.register(WorkLog)
