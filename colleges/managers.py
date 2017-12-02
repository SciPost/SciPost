import datetime

from django.db import models
from django.db.models import Q

today = datetime.date.today()


class FellowQuerySet(models.QuerySet):
    def guests(self):
        return self.filter(guest=True)

    def regular(self):
        return self.filter(guest=False)

    def active(self):
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True)
            ).order_by('contributor__user__last_name')

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
