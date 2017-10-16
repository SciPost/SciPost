import datetime

from django.db import models
from django.db.models import Q


class FellowQuerySet(models.QuerySet):
    def guests(self):
        return self.filter(guest=True)

    def regular(self):
        return self.filter(guest=False)

    def active(self):
        today = datetime.date.today()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True)
            ).order_by('contributor__user__last_name')

    def filter_for_submission_author(self, submission):
        try:
            submissions_exclude = Submission.objects.filter()
            Contributor.objects.filter(user__last_name)

            # return (self.exclude(authors=user.contributor)
            #         .exclude(Q(author_list__icontains=user.last_name),
            #                  ~Q(authors_false_claims=user.contributor)))
            return (self.exclude(contributor__in=submission.authors)
                    .exclude(Q(contributor__user__last_name=submission.author_list),  # U/S, use: https://docs.djangoproject.com/en/1.11/ref/models/querysets/#iregex
                             ~Q(contributor__in=submission.authors_false_claims.all())))
        except:
            return self.none()
