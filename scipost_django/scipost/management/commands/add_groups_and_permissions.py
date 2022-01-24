__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from scipost.models import Contributor


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
        Previewers, created = Group.objects.get_or_create(name='Previewers')
        NewsAdmin, created = Group.objects.get_or_create(name='News Administrators')
        Ambassadors, created = Group.objects.get_or_create(name='Ambassadors')
        JuniorAmbassadors, created = Group.objects.get_or_create(name='Junior Ambassadors')
        ProductionSupervisors, created = Group.objects.get_or_create(name='Production Supervisor')
        ProductionOfficers, created = Group.objects.get_or_create(name='Production Officers')

        OrgContacts, created = Group.objects.get_or_create(name='Organization Contacts')


        # Create Permissions
        content_type = ContentType.objects.get_for_model(Contributor)

        # Organizations
        can_manage_organizations, created = Permission.objects.get_or_create(
            codename='can_manage_organizations',
            name='Can manage Organizations',
            content_type=content_type)
        can_add_contactperson, created = Permission.objects.get_or_create(
            codename='can_add_contactperson',
            name='Can add ContactPerson',
            content_type=content_type)
        can_view_contactrole_list, created = Permission.objects.get_or_create(
            codename='can_view_contactrole_list',
            name='Can view ContactRole list',
            content_type=content_type)

        # Registration and invitations
        can_manage_contributors, created = Permission.objects.get_or_create(
            codename='can_manage_contributors',
            name='Can manage Contributors',
            content_type=content_type)
        can_vet_registration_requests, created = Permission.objects.get_or_create(
            codename='can_vet_registration_requests',
            name='Can vet registration requests',
            content_type=content_type)
        can_create_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_create_registration_invitations',
            name='Can create registration invitations',
            content_type=content_type)
        can_manage_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_manage_registration_invitations',
            name='Can manage registration invitations',
            content_type=content_type)
        can_invite_fellows, created = Permission.objects.get_or_create(
            codename='can_invite_fellows',
            name='Can invite Fellows',
            content_type=content_type)
        can_resend_registration_requests, created = Permission.objects.get_or_create(
            codename='can_resend_registration_requests',
            name='Can resend registration activation emails',
            content_type=content_type)
        can_read_all_privacy_sensitive_data, created = Permission.objects.get_or_create(
            codename='can_read_all_privacy_sensitive_data',
            name='Can read all privacy sensitive data',
            content_type=content_type)
        can_create_profiles, created = Permission.objects.get_or_create(
            codename='can_create_profiles',
            name='Can create Profiles',
            content_type=content_type)
        can_view_profiles, created = Permission.objects.get_or_create(
            codename='can_view_profiles',
            name='Can view Profiles',
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
        can_manage_college_composition, created = Permission.objects.get_or_create(
            codename='can_manage_college_composition',
            name='Can manage Editorial College compositions',
            content_type=content_type)
        can_attend_VGMs, created = Permission.objects.get_or_create(
            codename='can_attend_VGMs',
            name='Can attend Virtual General Meetings',
            content_type=content_type)
        can_view_potentialfellowship_list, created = Permission.objects.get_or_create(
            codename='can_view_potentialfellowship_list',
            name='Can view PotentialFellowship list',
            content_type=content_type)
        can_add_potentialfellowship, created = Permission.objects.get_or_create(
            codename='can_add_potentialfellowship',
            name='Can add PotentialFellowship',
            content_type=content_type)
        can_vote_on_potentialfellowship, created = Permission.objects.get_or_create(
            codename='can_vote_on_potentialfellowship',
            name='Can vote on PotentialFellowship',
            content_type=content_type)

        # Contributions (not related to submissions)
        can_submit_comments, created = Permission.objects.get_or_create(
            codename='can_submit_comments',
            name='Can submit Comments',
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
            content_type=content_type)

        # Submissions
        can_submit_manuscript, created = Permission.objects.get_or_create(
            codename='can_submit_manuscript',
            name='Can submit manuscript',
            content_type=content_type)
        can_do_plagiarism_checks, created = Permission.objects.get_or_create(
            codename='can_do_plagiarism_checks',
            name='Can do plagiarism checks on submissions',
            content_type=content_type)
        can_reassign_submissions, created = Permission.objects.get_or_create(
            codename='can_reassign_submissions',
            name='Can force-assign new EIC to Submission',
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
        can_manage_series, created = Permission.objects.get_or_create(
            codename='can_manage_series',
            name='Can manage Series and Collections',
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
        can_run_pre_screening, created = Permission.objects.get_or_create(
            codename='can_run_pre_screening',
            name='Can run pre-screening on Submissions',
            content_type=content_type)

        # Reports
        can_manage_reports, created = Permission.objects.get_or_create(
            codename='can_manage_reports',
            name='Can manage Reports',
            content_type=content_type)

        # Statistics
        can_view_statistics, created = Permission.objects.get_or_create(
            codename='can_view_statistics',
            name='Can view statistics',
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
        can_promote_user_to_production_officer, created = Permission.objects.get_or_create(
            codename='can_promote_user_to_production_officer',
            name='Can promote user to production officer',
            content_type=content_type)
        can_assign_production_officer, created = Permission.objects.get_or_create(
            codename='can_assign_production_officer',
            name='Can assign production officer',
            content_type=content_type)
        can_view_all_production_streams, created = Permission.objects.get_or_create(
            codename='can_view_all_production_streams',
            name='Can view all production stream',
            content_type=content_type)
        can_assign_production_supervisor, created = Permission.objects.get_or_create(
            codename='can_assign_production_supervisor',
            name='Can assign production supervisor',
            content_type=content_type)
        can_view_production, created = Permission.objects.get_or_create(
            codename='can_view_production',
            name='Can view production page',
            content_type=content_type)
        can_upload_proofs, created = Permission.objects.get_or_create(
            codename='can_upload_proofs',
            name='Can upload proofs',
            content_type=content_type)
        can_take_decisions_related_to_proofs, created = Permission.objects.get_or_create(
            codename='can_take_decisions_related_to_proofs',
            name='Can take decisions related to proofs',
            content_type=content_type)
        can_run_proofs_by_authors, created = Permission.objects.get_or_create(
            codename='can_run_proofs_by_authors',
            name='Can run proof by authors',
            content_type=content_type)
        can_manage_issues, created = Permission.objects.get_or_create(
            codename='can_manage_issues',
            name='Can manage Volumes and Issues',
            content_type=content_type)
        can_publish_accepted_submission, created = Permission.objects.get_or_create(
            codename='can_publish_accepted_submission',
            name='Can publish accepted submission',
            content_type=content_type)
        can_view_all_funding_info, created = Permission.objects.get_or_create(
            codename='can_view_all_funding_info',
            name='Can view all Funders info',
            content_type=content_type)
        can_create_grants, created = Permission.objects.get_or_create(
            codename='can_create_grants',
            name='Can create Grant',
            content_type=content_type)
        can_draft_publication, created = Permission.objects.get_or_create(
            codename='can_draft_publication',
            name='Can draft Publication',
            content_type=content_type)

        # Documentation
        can_view_docs_scipost, created = Permission.objects.get_or_create(
            codename='can_view_docs_scipost',
            name='Can view docs: scipost',
            content_type=content_type)

        # Financial administration
        can_manage_subsidies, created = Permission.objects.get_or_create(
            codename='can_manage_subsidies',
            name='Can manage subsidies',
            content_type=content_type)
        can_view_timesheets, created = Permission.objects.get_or_create(
            codename='can_view_timesheets',
            name='Can view timesheets',
            content_type=content_type)

        # News administration
        can_manage_news, created = Permission.objects.get_or_create(
            codename='can_manage_news',
            name='Can manage News',
            content_type=content_type)

        # Mailchimp
        can_manage_mailchimp, created = Permission.objects.get_or_create(
            codename='can_manage_mailchimp',
            name='Can manage Mailchimp settings',
            content_type=content_type)

        # Ontology
        can_manage_ontology, created = Permission.objects.get_or_create(
            codename='can_manage_ontology',
            name='Can manage ontology',
            content_type=content_type)

        # Previewing new features
        can_preview_new_features, created = Permission.objects.get_or_create(
            codename='can_preview_new_features',
            name='Can preview new features',
            content_type=content_type)

        # Assign permissions to groups
        SciPostAdmin.permissions.set([
            can_read_all_privacy_sensitive_data,
            can_manage_registration_invitations,
            can_create_registration_invitations,
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
            can_promote_user_to_production_officer,
            can_view_production,
            can_view_all_production_streams,
            can_attend_VGMs,
            can_view_timesheets,
            can_manage_mailchimp,
            can_view_statistics,
            can_create_profiles,
            can_view_profiles,
            can_manage_ontology,
            can_manage_organizations,
            can_view_potentialfellowship_list,
            can_add_potentialfellowship,
        ])

        FinancialAdmin.permissions.set([
            can_manage_organizations,
            can_manage_subsidies,
            can_view_timesheets,
        ])

        AdvisoryBoard.permissions.set([
            can_manage_registration_invitations,
            can_create_registration_invitations,
            can_attend_VGMs,
            can_view_statistics,
            can_view_potentialfellowship_list,
            can_add_potentialfellowship,
        ])

        EditorialAdmin.permissions.set([
            can_view_pool,
            can_invite_fellows,
            can_assign_submissions,
            can_do_plagiarism_checks,
            can_oversee_refereeing,
            can_reassign_submissions,
            can_run_pre_screening,
            can_manage_series,
            can_prepare_recommendations_for_voting,
            can_manage_college_composition,
            can_fix_College_decision,
            can_view_timesheets,
            can_publish_accepted_submission,
            can_manage_issues,
            can_draft_publication,
            can_view_all_funding_info,
            can_create_grants,
            can_attend_VGMs,
            can_manage_reports,
            can_assign_production_supervisor,
            can_view_all_production_streams,
            can_view_production,
            can_promote_user_to_production_officer,
            can_take_decisions_related_to_proofs,
            can_upload_proofs,
            can_run_proofs_by_authors,
            can_view_statistics,
            can_create_profiles,
            can_view_profiles,
            can_manage_ontology,
            can_manage_organizations,
            can_view_potentialfellowship_list,
            can_add_potentialfellowship,
        ])

        EditorialCollege.permissions.set([
            can_view_pool,
            can_take_charge_of_submissions,
            can_create_profiles,
            can_view_profiles,
            can_attend_VGMs,
            can_view_statistics,
            can_manage_ontology,
            can_view_potentialfellowship_list,
            can_add_potentialfellowship,
            can_vote_on_potentialfellowship,
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
            can_request_commentary_pages,
            can_request_thesislinks,
            can_referee,
        ])

        Developers.permissions.set([
            can_view_docs_scipost,
        ])

        Previewers.permissions.set([
            can_preview_new_features,
        ])

        Ambassadors.permissions.set([
            can_create_registration_invitations,
            can_manage_registration_invitations,
        ])

        JuniorAmbassadors.permissions.set([
            can_create_registration_invitations,
        ])

        ProductionSupervisors.permissions.set([
            can_view_profiles,
            can_assign_production_officer,
            can_take_decisions_related_to_proofs,
            # can_draft_publication,
            # can_create_grants,
            can_view_all_production_streams,
            can_run_proofs_by_authors,
            can_view_docs_scipost,
            can_view_production,
            can_upload_proofs,
        ])

        ProductionOfficers.permissions.set([
            can_view_docs_scipost,
            can_view_production,
            can_upload_proofs,
        ])

        OrgContacts.permissions.set([
            can_add_contactperson,
            can_view_contactrole_list,
            ])

        if verbose:
            self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions.'))
