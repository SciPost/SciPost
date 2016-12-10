from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from scipost.models import Contributor

class Command(BaseCommand):
    help = 'Defines groups and permissions'
    
    def add_arguments(self, parser):
        """ Append arguments optionally for setup of Contributor roles """
        parser.add_argument('-u', '--setup-user', metavar='<username>', type=str, required=False, help='Username to make registered contributor')
        parser.add_argument('-a', '--make-admin', required=False, action='store_true', help='Grant admin permissions to user (superuser only)')
        parser.add_argument('-t', '--make-tester',  required=False, action='store_true', help='Grant test permissions to user')

    def handle(self, *args, **options):
        """ Append all user Groups and setup a Contributor roles to user """
        
        # Create Groups
        SciPostAdmin, created = Group.objects.get_or_create(name='SciPost Administrators')
        AdvisoryBoard, created = Group.objects.get_or_create(name='Advisory Board')
        EditorialAdmin, created = Group.objects.get_or_create(name='Editorial Administrators')
        EditorialCollege, created = Group.objects.get_or_create(name='Editorial College')
        VettingEditors, created = Group.objects.get_or_create(name='Vetting Editors')
        RegisteredContributors, created = Group.objects.get_or_create(name='Registered Contributors')
        Testers, created = Group.objects.get_or_create(name='Testers')
        Ambassadors, created = Group.objects.get_or_create(name='Ambassadors')
        JuniorAmbassadors, created = Group.objects.get_or_create(name='Junior Ambassadors')

        # Create Permissions
        content_type = ContentType.objects.get_for_model(Contributor)

        # Registration and invitations
        can_vet_registration_requests, created = Permission.objects.get_or_create(
            codename='can_vet_registration_requests',
            name= 'Can vet registration requests',
            content_type=content_type)
        can_draft_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_draft_registration_invitations',
            name= 'Can draft registration invitations',
            content_type=content_type)
        can_manage_registration_invitations, created = Permission.objects.get_or_create(
            codename='can_manage_registration_invitations',
            name= 'Can manage registration invitations',
            content_type=content_type)
        can_invite_Fellows, created = Permission.objects.get_or_create(
            codename='can_invite_Fellows',
            name= 'Can invite Fellows',
            content_type=content_type)

        # Communications
        can_email_group_members, created = Permission.objects.get_or_create(
            codename='can_email_group_members',
            name= 'Can email group members',
            content_type=content_type)
        can_email_particulars, created = Permission.objects.get_or_create(
            codename='can_email_particulars',
            name= 'Can email particulars',
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
        can_view_pool, created = Permission.objects.get_or_create(
            codename='can_view_pool',
            name= 'Can view Submissions Pool',
            content_type=content_type)
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
        can_fix_College_decision, created = Permission.objects.get_or_create(
            codename='can_fix_College_decision',
            name = 'Can fix the College voting decision',
            content_type=content_type)

        # Production
        can_publish_accepted_submission, created = Permission.objects.get_or_create(
            codename='can_publish_accepted_submission',
            name = 'Can publish accepted submission',
            content_type=content_type)

        # Assign permissions to groups
        SciPostAdmin.permissions.add(
            can_manage_registration_invitations,
            can_email_group_members,
            can_email_particulars,
            can_vet_registration_requests,
            can_vet_commentary_requests,
            can_vet_thesislink_requests,
            can_vet_authorship_claims,
            can_vet_comments,
            can_view_pool,
            can_assign_submissions,
            can_prepare_recommendations_for_voting,
            can_fix_College_decision,
        )
        AdvisoryBoard.permissions.add(
            can_manage_registration_invitations,
        )
        EditorialAdmin.permissions.add(
            can_view_pool,
            can_assign_submissions,
            can_prepare_recommendations_for_voting,
            can_fix_College_decision,
            can_publish_accepted_submission,
            )
        EditorialCollege.permissions.add(
            can_view_pool,
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
        Ambassadors.permissions.add(
            can_manage_registration_invitations,
        )
        JuniorAmbassadors.permissions.add(
            can_draft_registration_invitations,
        )

        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions.'))
        
        if options['setup_user']:
            # Username is given, check options
            try:
                user = User.objects.get(username=str(options['setup_user']))
                user.groups.add(RegisteredContributors)
                self.stdout.write(self.style.SUCCESS('Successfully setup %s as contributor.' % user))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING('User <%s> not found.' % options['update_user']))
                return
            
            if user.is_superuser and options['make_admin']:
                # Setup admin contributor
                user.groups.add(SciPostAdmin)
                self.stdout.write(self.style.SUCCESS('Successfully made %s admin.' % user))
            elif options['make_admin']:
                # Make admin failed, user not a superuser
                self.stdout.write(self.style.WARNING('User %s is not a superuser.' % user))
                
            if options['make_tester']:
                # Setup test contributor
                user.groups.add(Testers)
                self.stdout.write(self.style.SUCCESS('Successfully made %s tester.' % user))