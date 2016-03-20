from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from scipost.models import Contributor, Opinion

class ContributorInline(admin.StackedInline):
#class ContributorInline(admin.TabularInline):
    model = Contributor

class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline, 
        ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

#admin.site.register(Contributor)

admin.site.register(Opinion)
