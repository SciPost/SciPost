from django.db import models

from scipost.behaviors import TimeStampedModel

from .managers import ProceedingQuerySet


class Proceeding(TimeStampedModel):
    """
    A Proceeding is a special kind of Journal Issue.
    """
    journal = models.ForeignKey('journals.Journal')
    name = models.CharField(max_length=256)
    open_for_submission = models.BooleanField(default=True)

    fellowships = models.ManyToManyField('colleges.Fellowship', blank=True,
                                         limit_choices_to={'guest': True})

    objects = ProceedingQuerySet.as_manager()

    class Meta:
        default_related_name = 'proceedings'

    def __str__(self):
        return self.name
