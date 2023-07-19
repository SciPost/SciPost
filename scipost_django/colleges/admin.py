__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    College,
    Fellowship,
    PotentialFellowship,
    PotentialFellowshipEvent,
    FellowshipNomination,
    FellowshipNominationEvent,
    FellowshipNominationComment,
    FellowshipNominationVotingRound,
    FellowshipNominationVote,
    FellowshipNominationDecision,
    FellowshipInvitation,
)


admin.site.register(College)


def fellowhip_is_active(fellowship):
    return fellowship.is_active()


class FellowshipAdmin(admin.ModelAdmin):
    search_fields = ["contributor__user__last_name", "contributor__user__first_name"]
    list_display = (
        "__str__",
        "college",
        "status",
        "senior",
        fellowhip_is_active,
    )
    list_filter = ("status",)
    fellowhip_is_active.boolean = True
    date_hierarchy = "created"
    autocomplete_fields = [
        "contributor",
    ]


admin.site.register(Fellowship, FellowshipAdmin)


class PotentialFellowshipEventInline(admin.TabularInline):
    model = PotentialFellowshipEvent
    autocomplete_fields = [
        "potfel",
        "noted_by",
    ]


class PotentialFellowshipAdmin(admin.ModelAdmin):
    inlines = [
        PotentialFellowshipEventInline,
    ]
    list_display = ["__str__", "college", "status"]
    search_fields = ["profile__last_name", "profile__first_name"]
    autocomplete_fields = [
        "profile",
        "in_agreement",
        "in_abstain",
        "in_disagreement",
    ]


admin.site.register(PotentialFellowship, PotentialFellowshipAdmin)


class FellowshipNominationEventInline(admin.TabularInline):
    model = FellowshipNominationEvent
    extra = 0


class FellowshipNominationCommentInline(admin.TabularInline):
    model = FellowshipNominationComment
    extra = 0


class FellowshipNominationVotingRoundInline(admin.TabularInline):
    model = FellowshipNominationVotingRound
    extra = 0


class FellowshipNominationDecisionInline(admin.TabularInline):
    model = FellowshipNominationDecision
    extra = 0


class FellowshipInvitationInline(admin.TabularInline):
    model = FellowshipInvitation
    extra = 0


class FellowshipNominationAdmin(admin.ModelAdmin):
    inlines = [
        FellowshipNominationEventInline,
        FellowshipNominationCommentInline,
        FellowshipNominationVotingRoundInline,
        FellowshipInvitationInline,
    ]
    list_filter = ["college__name"]
    list_display = ["profile", "college", "nominated_on"]
    search_fields = ["college__name", "profile__last_name", "profile__first_name"]
    autocomplete_fields = ["profile", "nominated_by", "fellowship"]


admin.site.register(FellowshipNomination, FellowshipNominationAdmin)


class FellowshipNominationVoteInline(admin.TabularInline):
    model = FellowshipNominationVote
    extra = 0


class FellowshipNominationVotingRoundAdmin(admin.ModelAdmin):
    model = FellowshipNominationVotingRound
    inlines = [
        FellowshipNominationVoteInline,
        FellowshipNominationDecisionInline,
    ]
    search_fields = [
        "nomination__profile__last_name",
        "nomination__profile__first_name",
        "nomination__college__name",
    ]
    list_display = [
        "nomination",
        "voting_opens",
        "voting_deadline",
        "is_open_checkmark",
        "decision__outcome",
    ]
    autocomplete_fields = [
        "nomination",
        "eligible_to_vote",
    ]
    list_filter = ("decision__outcome",)

    def decision__outcome(self, obj):
        return obj.decision.get_outcome_display()

    @admin.display(
        boolean=True,
        description="Open",
    )
    def is_open_checkmark(self, obj):
        return obj.is_open


admin.site.register(
    FellowshipNominationVotingRound, FellowshipNominationVotingRoundAdmin
)
