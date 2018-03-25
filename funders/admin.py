__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Funder, Grant


admin.site.register(Funder)


admin.site.register(Grant)
