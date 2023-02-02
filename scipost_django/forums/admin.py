__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import Forum, Meeting, Post, Motion


class ForumAdmin(GuardedModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    autocomplete_fields = [
        "moderators",
    ]


admin.site.register(Forum, ForumAdmin)


class MeetingAdmin(GuardedModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description", "preamble"]
    autocomplete_fields = [
        "moderators",
    ]


admin.site.register(Meeting, MeetingAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = ["anchor", "posted_by", "posted_on"]
    search_fields = ["posted_by__last_name", "subject", "text"]
    autocomplete_fields = [
        "posted_by",
        "vetted_by",
        "cf_latest_followup_in_hierarchy",
    ]


admin.site.register(Post, PostAdmin)


class MotionAdmin(admin.ModelAdmin):
    search_fields = ["posted_by__last_name", "subject", "text"]
    autocomplete_fields = [
        "posted_by",
        "vetted_by",
        "post",
        "eligible_for_voting",
        "in_agreement",
        "in_doubt",
        "in_disagreement",
        "in_abstain",
    ]


admin.site.register(Motion, MotionAdmin)
