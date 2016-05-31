from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from guardian.admin import GuardedModelAdmin

from scipost.models import *

#admin.site.register(Contributor)

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


class RegistrationInvitationAdmin(admin.ModelAdmin):
    search_fields = ['last_name', 'email']

admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)


admin.site.register(AuthorshipClaim)
#admin.site.register(Opinion)

admin.site.register(Permission)

class ListAdmin(GuardedModelAdmin):
    search_fields = ['owner', 'title']

admin.site.register(List, ListAdmin)

admin.site.register(Team)

#admin.site.register(Graph)

#admin.site.register(Node)

#admin.site.register(Arc)

class NodeInline(admin.StackedInline):
    model = Node

class ArcInline(admin.StackedInline):
    model = Arc
    
class GraphAdmin(GuardedModelAdmin):
    inlines = [
        NodeInline,
        ArcInline,
        ]
    search_fields = ['owner___user__last_name', 'title']

admin.site.register(Graph, GraphAdmin)
