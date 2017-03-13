from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from guardian.admin import GuardedModelAdmin

from scipost.models import Contributor, Remark, List,\
                           DraftInvitation, Node, Arc, Graph, Team, AffiliationObject,\
                           SupportingPartner, SPBMembershipAgreement, RegistrationInvitation,\
                           AuthorshipClaim, PrecookedEmail
from virtualmeetings.models import VGM, Feedback, Nomination, Motion


class ContributorInline(admin.StackedInline):
    model = Contributor


class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline,
        ]
    search_fields = ['last_name', 'email']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# class VGMAdmin(admin.ModelAdmin):
#     search_fields = ['start_date']
#
#
# admin.site.register(VGM, VGMAdmin)
#
#
# class FeedbackAdmin(admin.ModelAdmin):
#     search_fields = ['feedback', 'by']
#
#
# admin.site.register(Feedback, FeedbackAdmin)
#
#
# class NominationAdmin(admin.ModelAdmin):
#     search_fields = ['last_name', 'first_name', 'by']
#
#
# admin.site.register(Nomination, NominationAdmin)
#
#
# class MotionAdmin(admin.ModelAdmin):
#     search_fields = ['background', 'motion', 'put_forward_by']
#
#
# admin.site.register(Motion, MotionAdmin)


class RemarkAdmin(admin.ModelAdmin):
    search_fields = ['contributor', 'remark']


admin.site.register(Remark, RemarkAdmin)


class DraftInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'processed']


admin.site.register(DraftInvitation, DraftInvitationAdmin)


class RegistrationInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'invitation_key']


admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)


admin.site.register(AuthorshipClaim)
admin.site.register(Permission)


class PrecookedEmailAdmin(admin.ModelAdmin):
    search_fields = ['email_subject', 'email_text', 'emailed_to']


admin.site.register(PrecookedEmail, PrecookedEmailAdmin)


class ListAdmin(GuardedModelAdmin):
    search_fields = ['owner', 'title']


admin.site.register(List, ListAdmin)
admin.site.register(Team)


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


class AffiliationObjectAdmin(admin.ModelAdmin):
    search_fields = ['country', 'institution', 'subunit']


admin.site.register(AffiliationObject, AffiliationObjectAdmin)


class SPBMembershipAgreementInline(admin.StackedInline):
    model = SPBMembershipAgreement


class SupportingPartnerAdmin(admin.ModelAdmin):
    search_fields = ['institution', 'institution_acronym',
                     'institution_address', 'contact_person']
    inlines = [
        SPBMembershipAgreementInline,
    ]


admin.site.register(SupportingPartner, SupportingPartnerAdmin)
