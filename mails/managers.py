from django.db import models


class MailLogQuerySet(models.QuerySet):
    def not_sent(self):
        return self.filter(status__in=['not_rendered',  'rendered'])

    def unrendered(self):
        return self.filter(status='not_rendered')

    def rendered(self):
        return self.filter(status='rendered')
