from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from scipost.models import Contributor

class Command(BaseCommand):
    help = 'Defines groups and permissions'

    def handle(self, *args, **options):
        # Create Groups
        SciPostAdmin, created = Group.objects.get_or_create(name='SciPost Administrators')
        AdvisoryBoard, created = Group.objects.get_or_create(name='Advisory Board')
        EditorialAdmin, created = Group.objects.get_or_create(name='Editorial Administrators') 
        EditorialCollege, created = Group.objects.get_or_create(name='Editorial College')
        VettingEditors, created = Group.objects.get_or_create(name='Vetting Editors')
        RegisteredContributors, created = Group.objects.get_or_create(name='Registered Contributors')
        Testers, created = Group.objects.get_or_create(name='Testers')

        # Create Permissions
        content_type = ContentType.objects.get_for_model(Contributor)

        # Registration
        can_vet_registration_requests, created = Permission.objects.get_or_create(
            codename='can_vet_registration_requests',
            name= 'Can vet registration requests',
            content_type=content_type)
        can_manage_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_manage_registration_invitations',
            name= 'Can manage registration invitations',
            content_type=content_type)

        # Editorial College
        view_bylaws, created = Permission.objects.get_or_create(
            codename='view_bylaws',
            name= 'Can view By-laws of Editorial College',
            content_type=content_type)
        #can_take_editorial_actions, created = Permission.objects.get_or_create(
        #    codename='can_take_editorial_actions',
        #    name= 'Can take editorial actions',
        #    content_type=content_type)
        
        # Contributions (not related to submissions)
        can_submit_comments, created = Permission.objects.get_or_create(
            codename='can_submit_comments',
            name= 'Can submit Comments',
            content_type=content_type)
        can_express_opinion_on_comments, created = Permission.objects.get_or_create(
            codename='can_express_opinion_on_comments',
            name= 'Can express opinion on Comments',
            content_type=content_type)
        can_request_commentary_pages, created = Permission.objects.get_or_create(
            codename='can_request_commentary_pages',
            name= 'Can request opening of Commentara Pages',
            content_type=content_type)
        can_request_thesislinks, created = Permission.objects.get_or_create(
            codename='can_request_thesislinks',
            name= 'Can request Thesis Links',
            content_type=content_type)

        # Vetting of simple objects
        can_vet_commentary_requests, created = Permission.objects.get_or_create(
            codename='can_vet_commentary_requests',
            name= 'Can vet Commentary page requests',
            content_type=content_type)
        can_vet_thesislink_requests, created = Permission.objects.get_or_create(
            codename='can_vet_thesislink_requests',
            name= 'Can vet Thesis Link requests',
            content_type=content_type)
        can_vet_authorship_claims, created = Permission.objects.get_or_create(
            codename='can_vet_authorship_claims',
            name= 'Can vet Authorship claims',
            content_type=content_type)
        can_vet_comments, created = Permission.objects.get_or_create(
            codename='can_vet_comments',
            name= 'Can vet submitted Comments',
            content_type=content_type)

        # Submissions
        can_submit_manuscript, created = Permission.objects.get_or_create(
            codename='can_submit_manuscript',
            name='Can submit manuscript',
            content_type=content_type)

        # Submission handling
        can_assign_submissions, created = Permission.objects.get_or_create(
            codename='can_assign_submissions',
            name= 'Can assign incoming Submissions to potential Editor-in-charge',
            content_type=content_type)
        can_take_charge_of_submissions, created = Permission.objects.get_or_create(
            codename='can_take_charge_of_submissions',
            name= 'Can take charge (become Editor-in-charge) of submissions',
            content_type=content_type)
        can_vet_submitted_reports, created = Permission.objects.get_or_create(
            codename='can_vet_submitted_reports', 
            name='Can vet submitted Reports', 
            content_type=content_type)

        # Refereeing
        can_referee, created = Permission.objects.get_or_create(
            codename='can_referee',
            name= 'Can act as a referee and submit reports on Submissions',
            content_type=content_type)

        # Voting
        can_prepare_recommendations_for_voting, created = Permission.objects.get_or_create(
            codename='can_prepare_recommendations_for_voting',
            name = 'Can prepare recommendations for voting',
            content_type=content_type)

        # Assign permissions to groups
        SciPostAdmin.permissions.add(
            can_manage_registration_invitations,
            can_vet_registration_requests,
            can_vet_commentary_requests, 
            can_vet_thesislink_requests,
            can_vet_authorship_claims, 
            can_vet_comments,
            can_assign_submissions,
            can_prepare_recommendations_for_voting,
        )
        EditorialAdmin.permissions.add(
            can_assign_submissions,
            can_prepare_recommendations_for_voting,
            )
        EditorialCollege.permissions.add(
            can_take_charge_of_submissions,
            #can_take_editorial_actions,
            can_vet_submitted_reports,
            view_bylaws,
        )
        VettingEditors.permissions.add(
            can_vet_commentary_requests, 
            can_vet_thesislink_requests,
            can_vet_authorship_claims, 
            can_vet_comments,
        )
        RegisteredContributors.permissions.add(
            can_submit_manuscript,
            can_submit_comments, 
            can_express_opinion_on_comments,
            can_request_commentary_pages,
            can_request_thesislinks,
            can_referee,
        )

        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions'))
