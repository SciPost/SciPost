import datetime

from django.db import models
from django.utils import timezone


class ThesisLinkManager(models.Manager):
    def search_results(self, form):
        from_date = form.cleaned_data['from_date'] if form.cleaned_data['from_date'] else datetime.date(1600, 1, 1)
        to_date = form.cleaned_data['to_date'] if form.cleaned_data['to_date'] else timezone.now()

        return self.vetted().filter(
            title__icontains=form.cleaned_data['title_keyword'],
            author__icontains=form.cleaned_data['author'],
            abstract__icontains=form.cleaned_data['abstract_keyword'],
            supervisor__icontains=form.cleaned_data['supervisor'],
            defense_date__range=(from_date, to_date)
        ).order_by('-defense_date')

    def latest(self, n):
        return self.vetted().order_by('latest_activity')[:n]

    def vetted(self):
        return self.filter(vetted=True)
