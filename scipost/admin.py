from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from guardian.admin import GuardedModelAdmin

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

class ListAdmin(GuardedModelAdmin):
    search_fields = ['owner', 'title']

admin.site.register(List, ListAdmin)

admin.site.register(Team)

admin.site.register(Graph)

admin.site.register(Node)
