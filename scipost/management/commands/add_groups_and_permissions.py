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
        EditorialCollege, created = Group.objects.get_or_create(name='Editorial College')
        VettingEditors, created = Group.objects.get_or_create(name='Vetting Editors')
        RegisteredContributors, created = Group.objects.get_or_create(name='Registered Contributors')

        # Create Permissions
        content_type = ContentType.objects.get_for_model(Contributor)
        # Registration
        can_manage_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_manage_registration_invitations',
            name= 'Can manage registration invitations',
            content_type=content_type)
        can_vet_registration_requests, created = Permission.objects.get_or_create(
            codename='can_vet_registration_requests',
            name= 'Can vet registration requests',
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
        # Submission handling
        can_process_incoming_submissions, created = Permission.objects.get_or_create(
            codename='can_process_incoming_submissions',
            name= 'Can process incoming Submissions',
            content_type=content_type)
        can_vet_submitted_reports, created = Permission.objects.get_or_create(
            codename='can_vet_submitted_reports', 
            name='Can vet submitted Reports', 
            content_type=content_type)

        # Assign permissions to groups
        SciPostAdmin.permissions.add(can_manage_registration_invitations,
                                     can_vet_registration_requests,
                                     can_vet_commentary_requests, 
                                     can_vet_thesislink_requests,
                                     can_vet_authorship_claims, 
                                     can_vet_comments,
                                     )
        VettingEditors.permissions.add(can_vet_commentary_requests, 
                                       can_vet_thesislink_requests,
                                       can_vet_authorship_claims, 
                                       can_vet_comments,
                                       )

        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions'))
