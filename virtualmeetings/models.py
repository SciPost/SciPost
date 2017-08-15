from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import timezone

from .constants import MOTION_CATEGORIES

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor


class VGM(models.Model):
    """
    Each year, a Virtual General Meeting is held during which operations at
    SciPost are discussed. A VGM can be attended by Administrators,
    Advisory Board members and Editorial Fellows.
    """
    start_date = models.DateField()
    end_date = models.DateField()
    information = models.TextField(default='')

    def __str__(self):
        return 'From %s to %s' % (self.start_date.strftime('%Y-%m-%d'),
                                  self.end_date.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        return reverse('virtualmeetings:VGM_detail', args=(self.id,))


class Feedback(models.Model):
    """
    Feedback, suggestion or criticism on any aspect of SciPost.
    """
    VGM = models.ForeignKey('virtualmeetings.VGM', blank=True, null=True)
    by = models.ForeignKey('scipost.Contributor')
    date = models.DateField()
    feedback = models.TextField()

    def __str__(self):
        return '%s: %s' % (self.by, self.feedback[:50])

    def get_absolute_url(self):
        return self.VGM.get_absolute_url() + '#feedback' + str(self.id)

    def as_li(self):
        raise DeprecationWarning


class Nomination(models.Model):
    """
    Nomination to an Editorial Fellowship.
    """
    VGM = models.ForeignKey('virtualmeetings.VGM', blank=True, null=True)
    by = models.ForeignKey('scipost.Contributor')
    date = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default='physics', verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    webpage = models.URLField()
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField('scipost.Contributor',
                                          related_name='in_agreement_with_nomination', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField('scipost.Contributor',
                                        related_name='in_notsure_with_nomination', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField('scipost.Contributor',
                                             related_name='in_disagreement_with_nomination',
                                             blank=True)
    voting_deadline = models.DateTimeField('voting deadline', default=timezone.now)
    accepted = models.NullBooleanField()

    def __str__(self):
        return '%s %s (nominated by %s)' % (self.first_name,
                                            self.last_name,
                                            self.by)

    def get_absolute_url(self):
        return self.VGM.get_absolute_url() + '#nomination_' + str(self.id)

    def as_li(self):
        raise DeprecationWarning

    def votes_as_ul(self):
        raise DeprecationWarning

    def update_votes(self, contributor_id, vote):
        contributor = get_object_or_404(Contributor, pk=contributor_id)
        self.in_agreement.remove(contributor)
        self.in_notsure.remove(contributor)
        self.in_disagreement.remove(contributor)
        if vote == 'A':
            self.in_agreement.add(contributor)
        elif vote == 'N':
            self.in_notsure.add(contributor)
        elif vote == 'D':
            self.in_disagreement.add(contributor)
        self.nr_A = self.in_agreement.count()
        self.nr_N = self.in_notsure.count()
        self.nr_D = self.in_disagreement.count()
        self.save()


class Motion(models.Model):
    """
    Motion instances are put forward to the Advisory Board and Editorial College
    and detail suggested changes to rules, procedures etc.
    They are meant to be voted on at the annual VGM.
    """
    category = models.CharField(max_length=10, choices=MOTION_CATEGORIES, default='General')
    VGM = models.ForeignKey('virtualmeetings.VGM', blank=True, null=True)
    background = models.TextField()
    motion = models.TextField()
    put_forward_by = models.ForeignKey('scipost.Contributor')
    date = models.DateField(auto_now_add=True)
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField('scipost.Contributor',
                                          related_name='in_agreement_with_motion', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField('scipost.Contributor',
                                        related_name='in_notsure_with_motion', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField('scipost.Contributor',
                                             related_name='in_disagreement_with_motion',
                                             blank=True)
    voting_deadline = models.DateTimeField('voting deadline', default=timezone.now)
    accepted = models.NullBooleanField()

    def __str__(self):
        return self.motion[:32]

    def get_absolute_url(self):
        return self.VGM.get_absolute_url() + '#motion_' + str(self.id)

    def as_li(self):
        raise DeprecationWarning

    def votes_as_ul(self):
        raise DeprecationWarning

    def update_votes(self, contributor_id, vote):
        contributor = get_object_or_404(Contributor, pk=contributor_id)
        self.in_agreement.remove(contributor)
        self.in_notsure.remove(contributor)
        self.in_disagreement.remove(contributor)
        if vote == 'A':
            self.in_agreement.add(contributor)
        elif vote == 'N':
            self.in_notsure.add(contributor)
        elif vote == 'D':
            self.in_disagreement.add(contributor)
        self.nr_A = self.in_agreement.count()
        self.nr_N = self.in_notsure.count()
        self.nr_D = self.in_disagreement.count()
        self.save()
