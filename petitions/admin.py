from django.contrib import admin

from .models import Petition, PetitionSignatory


class PetitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Petition, PetitionAdmin)


class PetitionSignatoryAdmin(admin.ModelAdmin):
    search_fields = ['last_name', 'country', 'institution']


admin.site.register(PetitionSignatory, PetitionSignatoryAdmin)
