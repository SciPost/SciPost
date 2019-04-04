__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management import BaseCommand



class Command(BaseCommand):
    """Update/Reindex all Haystack's search indices."""

    help = 'Update/Reindex all Haystack's search indices'

    def handle(self, *args, **kwargs):
        
        count = 0

        for fellow in fellows:
            nr_potfels_to_vote_on = PotentialFellowship.objects.to_vote_on(fellow).count()
            recs_to_vote_on = EICRecommendation.objects.user_must_vote_on(fellow.user)
            assignments_ongoing = fellow.editorial_assignments.ongoing()
            assignments_to_consider = fellow.editorial_assignments.invited()
            assignments_upcoming_deadline = assignments_ongoing.refereeing_deadline_within(days=7)
            if recs_to_vote_on or assignments_ongoing or assignments_to_consider or assignments_upcoming_deadline:
                mail_sender = DirectMailUtil(
                    'fellows/email_fellow_tasklist',
                    # Render immediately, because m2m/querysets cannot be saved for later rendering:
                    delayed_processing=False,
                    object=fellow,
                    fellow=fellow,
                    nr_potfels_to_vote_on=nr_potfels_to_vote_on,
                    recs_to_vote_on=recs_to_vote_on,
                    assignments_ongoing=assignments_ongoing,
                    assignments_to_consider=assignments_to_consider,
                    assignments_upcoming_deadline=assignments_upcoming_deadline)
                mail_sender.send_mail()
                count += 1
        self.stdout.write(self.style.SUCCESS('Emailed {} fellows.'.format(count)))
