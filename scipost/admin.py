from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from scipost.models import *

class ContributorInline(admin.StackedInline):
#class ContributorInline(admin.TabularInline):
    model = Contributor

class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline, 
        ]
    search_fields = ['last_name', 'email']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(RegistrationInvitation)

#admin.site.register(Contributor)

admin.site.register(AuthorshipClaim)
#admin.site.register(Opinion)

admin.site.register(Permission)

admin.site.register(List)

admin.site.register(Team)

admin.site.register(Graph)

admin.site.register(Node)
