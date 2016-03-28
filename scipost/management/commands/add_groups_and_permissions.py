from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Defines groups and permissions'

    def handle(self, *args, **options):
        SciPostAdmin, created = Group.objects.get_or_create(name='SciPost Administrators')
        AdvisoryBoard, created = Group.objects.get_or_create(name='Advisory Board')
        EditorialCollege, created = Group.objects.get_or_create(name='Editorial College')
        VettingEditors, created = Group.objects.get_or_create(name='Vetting Editors')
        RegisteredContributors, created = Group.objects.get_or_create(name='Registered Contributors')
        # Registration
        can_manage_registration_invitations = Permission.objects.get(codename='can_manage_registration_invitations')
        can_vet_registration_requests = Permission.objects.get(codename='can_vet_registration_requests')
        # Vetting of simple objects
        can_vet_commentary_requests = Permission.objects.get(codename='can_vet_commentary_requests')
        can_vet_thesislink_requests = Permission.objects.get(codename='can_vet_thesislink_requests')
        can_vet_authorship_claims = Permission.objects.get(codename='can_vet_authorship_claims')
        can_vet_comments = Permission.objects.get(codename='can_vet_comments')
        # Submission handling
        can_process_incoming_submissions = Permission.objects.get(codename='can_process_incoming_submissions')
        can_vet_submitted_reports = Permission.objects.get(codename='can_vet_submitted_reports')
        SciPostAdmin.permissions.add(can_manage_registration_invitations,
                                     can_vet_registration_requests,
                                     can_vet_commentary_requests, can_vet_thesislink_requests,
                                     can_vet_authorship_claims, can_vet_comments,
                                     )
        VettingEditors.permissions.add(can_vet_commentary_requests, can_vet_thesislink_requests,
                                       can_vet_authorship_claims, can_vet_comments,
                                       )
        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions'))
