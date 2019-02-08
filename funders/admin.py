__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Funder, Grant


admin.site.register(Funder)


admin.site.register(Grant)
