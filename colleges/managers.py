__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING


class FellowQuerySet(models.QuerySet):
    def guests(self):
        return self.filter(guest=True)

    def regular(self):
        return self.filter(guest=False)

    def active(self):
        today = timezone.now().date()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True)
            ).ordered()

    def ordered(self):
        """Return ordered queryset explicitly, since this may have big affect on performance."""
        return self.order_by('contributor__user__last_name')

    def return_active_for_submission(self, submission):
        """
        This method returns a *list* of Fellowships that passed the 'author-check' for
        a specific submission.
        """
        try:
            qs = self.exclude(contributor__in=submission.authors.all()).active()
            false_claims = submission.authors_false_claims.all()
            author_list = submission.author_list.lower()
            fellowships = []
            for fellowship in qs:
                contributor = fellowship.contributor
                user = contributor.user
                if user.last_name.lower() in author_list and contributor not in false_claims:
                    continue

                fellowships.append(fellowship)
            return fellowships
        except AttributeError:
                return []


class PotentialFellowshipQuerySet(models.QuerySet):
    def vote_needed(self, contributor):
        return self.filter(
            profile__discipline=contributor.profile.discipline,
            status=POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING
        ).order_by('profile__last_name')

    def to_vote_on(self, contributor):
        return self.vote_needed(contributor).exclude(
            Q(in_agreement__in=[contributor]) |
            Q(in_abstain__in=[contributor]) |
            Q(in_disagreement__in=[contributor]))

    def voted_on(self, contributor):
        return self.vote_needed(contributor).filter(
            Q(in_agreement__in=[contributor]) |
            Q(in_abstain__in=[contributor]) |
            Q(in_disagreement__in=[contributor]))
