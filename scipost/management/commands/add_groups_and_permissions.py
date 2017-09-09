from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from partners.models import Contact
from scipost.models import Contributor, DraftInvitation
from submissions.models import Report


class Command(BaseCommand):
    help = 'Defines groups and permissions'

    def handle(self, *args, verbose=True, **options):
        """Append all user Groups and setup a Contributor roles to user."""

        # Create Groups
        SciPostAdmin, created = Group.objects.get_or_create(name='SciPost Administrators')
        FinancialAdmin, created = Group.objects.get_or_create(name='Financial Administrators')
        AdvisoryBoard, created = Group.objects.get_or_create(name='Advisory Board')
        EditorialAdmin, created = Group.objects.get_or_create(name='Editorial Administrators')
        EditorialCollege, created = Group.objects.get_or_create(name='Editorial College')
        VettingEditors, created = Group.objects.get_or_create(name='Vetting Editors')
        RegisteredContributors, created = Group.objects.get_or_create(
                                                            name='Registered Contributors')
        Developers, created = Group.objects.get_or_create(name='Developers')
        Testers, created = Group.objects.get_or_create(name='Testers')
        Ambassadors, created = Group.objects.get_or_create(name='Ambassadors')
        JuniorAmbassadors, created = Group.objects.get_or_create(name='Junior Ambassadors')
        ProductionOfficers, created = Group.objects.get_or_create(name='Production Officers')

        PartnersAdmin, created = Group.objects.get_or_create(name='Partners Administrators')
        PartnersOfficers, created = Group.objects.get_or_create(name='Partners Officers')
        PartnerAccounts, created = Group.objects.get_or_create(name='Partners Accounts')

        # Create Permissions
        content_type = ContentType.objects.get_for_model(Contributor)
        content_type_contact = ContentType.objects.get_for_model(Contact)
        content_type_draft_invitation = ContentType.objects.get_for_model(DraftInvitation)
        content_type_report = ContentType.objects.get_for_model(Report)

        # Supporting Partners
        can_manage_SPB, created = Permission.objects.get_or_create(
            codename='can_manage_SPB',
            name='Can manage Supporting Partners Board',
            content_type=content_type)
        can_email_prospartner_contact, created = Permission.objects.get_or_create(
            codename='can_email_prospartner_contact',
            name='Can email Prospective Partner Contact',
            content_type=content_type)
        can_read_partner_page, created = Permission.objects.get_or_create(
            codename='can_read_partner_page',
            name='Can read Prospective Partner personal page',
            content_type=content_type)
        can_promote_prospect_to_partner, created = Permission.objects.get_or_create(
            codename='can_promote_prospect_to_partner',
            name='Can promote Prospective Partner to Partner',
            content_type=content_type)
        can_view_partners, created = Permission.objects.get_or_create(
            codename='can_view_partners',
            name='Can view Partner details of all Partners',
            content_type=content_type)
        can_view_own_partner_details, created = Permission.objects.get_or_create(
            codename='can_view_own_partner_details',
            name='Can view (its own) partner details',
            content_type=content_type)

        # Registration and invitations
        change_draft_invitation, created = Permission.objects.get_or_create(
            codename='change_draftinvitation',
            defaults={
                'name': 'Can vet registration requests',
                'content_type': content_type_draft_invitation
            }
        )
        can_vet_registration_requests, created = Permission.objects.get_or_create(
            codename='can_vet_registration_requests',
            name='Can vet registration requests',
            content_type=content_type)
        can_draft_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_draft_registration_invitations',
            name='Can draft registration invitations',
            content_type=content_type)
        can_manage_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_manage_registration_invitations',
            name='Can manage registration invitations',
            content_type=content_type)
        can_invite_Fellows, created = Permission.objects.get_or_create(
            codename='can_invite_Fellows',
            name='Can invite Fellows',
            content_type=content_type)
        can_resend_registration_requests, created = Permission.objects.get_or_create(
            codename='can_resend_registration_requests',
            name='Can resend registration activation emails',
            content_type=content_type)

        # Communications
        can_email_group_members, created = Permission.objects.get_or_create(
            codename='can_email_group_members',
            name='Can email group members',
            content_type=content_type)
        can_email_particulars, created = Permission.objects.get_or_create(
            codename='can_email_particulars',
            name='Can email particulars',
            content_type=content_type)

        # Editorial College
        can_attend_VGMs, created = Permission.objects.get_or_create(
            codename='can_attend_VGMs',
            name='Can attend Virtual General Meetings',
            content_type=content_type)

        # Contributions (not related to submissions)
        can_submit_comments, created = Permission.objects.get_or_create(
            codename='can_submit_comments',
            name='Can submit Comments',
            content_type=content_type)
        can_express_opinion_on_comments, created = Permission.objects.get_or_create(
            codename='can_express_opinion_on_comments',
            name='Can express opinion on Comments',
            content_type=content_type)
        can_request_commentary_pages, created = Permission.objects.get_or_create(
            codename='can_request_commentary_pages',
            name='Can request opening of Commentara Pages',
            content_type=content_type)
        can_request_thesislinks, created = Permission.objects.get_or_create(
            codename='can_request_thesislinks',
            name='Can request Thesis Links',
            content_type=content_type)

        # Vetting of objects
        can_vet_commentary_requests, created = Permission.objects.get_or_create(
            codename='can_vet_commentary_requests',
            name='Can vet Commentary page requests',
            content_type=content_type)
        can_vet_thesislink_requests, created = Permission.objects.get_or_create(
            codename='can_vet_thesislink_requests',
            name='Can vet Thesis Link requests',
            content_type=content_type)
        can_vet_authorship_claims, created = Permission.objects.get_or_create(
            codename='can_vet_authorship_claims',
            name='Can vet Authorship claims',
            content_type=content_type)
        can_vet_comments, created = Permission.objects.get_or_create(
            codename='can_vet_comments',
            name='Can vet submitted Comments',
            content_type=content_type)
        can_vet_submitted_reports, created = Permission.objects.get_or_create(
            codename='can_vet_submitted_reports',
            name='Can vet submitted Reports',
            content_type=content_type_report)

        # Submissions
        can_submit_manuscript, created = Permission.objects.get_or_create(
            codename='can_submit_manuscript',
            name='Can submit manuscript',
            content_type=content_type)
        can_do_plagiarism_checks, created = Permission.objects.get_or_create(
            codename='can_do_plagiarism_checks',
            name='Can do plagiarism checks on submissions',
            content_type=content_type)

        # Submission handling
        can_view_pool, created = Permission.objects.get_or_create(
            codename='can_view_pool',
            name='Can view Submissions Pool',
            content_type=content_type)
        can_assign_submissions, created = Permission.objects.get_or_create(
            codename='can_assign_submissions',
            name='Can assign incoming Submissions to potential Editor-in-charge',
            content_type=content_type)
        can_take_charge_of_submissions, created = Permission.objects.get_or_create(
            codename='can_take_charge_of_submissions',
            name='Can take charge (become Editor-in-charge) of submissions',
            content_type=content_type)

        # Refereeing
        can_referee, created = Permission.objects.get_or_create(
            codename='can_referee',
            name='Can act as a referee and submit reports on Submissions',
            content_type=content_type)
        can_oversee_refereeing, created = Permission.objects.get_or_create(
            codename='can_oversee_refereeing',
            name='Can oversee refereeing',
            content_type=content_type)

        # Reports
        can_manage_reports, created = Permission.objects.get_or_create(
            codename='can_manage_reports',
            name='Can manage Reports',
            content_type=content_type)

        # Voting
        can_prepare_recommendations_for_voting, created = Permission.objects.get_or_create(
            codename='can_prepare_recommendations_for_voting',
            name='Can prepare recommendations for voting',
            content_type=content_type)
        can_fix_College_decision, created = Permission.objects.get_or_create(
            codename='can_fix_College_decision',
            name='Can fix the College voting decision',
            content_type=content_type)

        # Production
        can_view_production, created = Permission.objects.get_or_create(
            codename='can_view_production',
            name='Can view production page',
            content_type=content_type)
        can_publish_accepted_submission, created = Permission.objects.get_or_create(
            codename='can_publish_accepted_submission',
            name='Can publish accepted submission',
            content_type=content_type)

        # Documentation
        can_view_docs_scipost, created = Permission.objects.get_or_create(
            codename='can_view_docs_scipost',
            name='Can view docs: scipost',
            content_type=content_type)

        # Financial administration
        can_view_timesheets, created = Permission.objects.get_or_create(
            codename='can_view_timesheets',
            name='Can view timesheets',
            content_type=content_type)

        # Mailchimp
        can_manage_mailchimp, created = Permission.objects.get_or_create(
            codename='can_manage_mailchimp',
            name='Can manage Mailchimp settings',
            content_type=content_type)

        # Assign permissions to groups
        SciPostAdmin.permissions.set([
            can_manage_registration_invitations,
            change_draft_invitation,
            can_email_group_members,
            can_email_particulars,
            can_resend_registration_requests,
            can_vet_registration_requests,
            can_vet_commentary_requests,
            can_vet_thesislink_requests,
            can_vet_authorship_claims,
            can_vet_submitted_reports,
            can_vet_comments,
            can_view_pool,
            can_assign_submissions,
            can_prepare_recommendations_for_voting,
            can_fix_College_decision,
            can_view_production,
            can_attend_VGMs,
            can_view_timesheets,
            can_manage_mailchimp,
        ])

        FinancialAdmin.permissions.set([
            can_view_timesheets,
        ])

        AdvisoryBoard.permissions.set([
            can_manage_registration_invitations,
            change_draft_invitation,
            can_attend_VGMs,
        ])

        EditorialAdmin.permissions.set([
            can_view_pool,
            can_assign_submissions,
            can_do_plagiarism_checks,
            can_oversee_refereeing,
            can_prepare_recommendations_for_voting,
            can_fix_College_decision,
            can_view_production,
            can_view_timesheets,
            can_publish_accepted_submission,
            can_attend_VGMs,
            can_manage_reports,
        ])

        EditorialCollege.permissions.set([
            can_view_pool,
            can_take_charge_of_submissions,
            can_attend_VGMs,
        ])

        VettingEditors.permissions.set([
            can_vet_commentary_requests,
            can_vet_thesislink_requests,
            can_vet_authorship_claims,
            can_vet_submitted_reports,
            can_vet_comments,
        ])

        RegisteredContributors.permissions.set([
            can_submit_manuscript,
            can_submit_comments,
            can_express_opinion_on_comments,
            can_request_commentary_pages,
            can_request_thesislinks,
            can_referee,
        ])

        Developers.permissions.set([
            can_view_docs_scipost,
        ])

        Ambassadors.permissions.set([
            can_manage_registration_invitations,
            change_draft_invitation,
        ])

        JuniorAmbassadors.permissions.set([
            can_draft_registration_invitations,
        ])

        ProductionOfficers.permissions.set([
            can_view_docs_scipost,
            can_view_production,
        ])

        PartnersAdmin.permissions.set([
            can_read_partner_page,
            can_view_own_partner_details,
            can_manage_SPB,
            can_promote_prospect_to_partner,
            can_email_prospartner_contact,
            can_view_partners,
        ])

        PartnersOfficers.permissions.set([
            can_read_partner_page,
            can_view_own_partner_details,
            can_manage_SPB,
            can_view_partners,
        ])

        PartnerAccounts.permissions.set([
            can_read_partner_page,
            can_view_own_partner_details,
        ])

        if verbose:
            self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions.'))
