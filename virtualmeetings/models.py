from django.db import models
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from django.utils import timezone

from .constants import MOTION_CATEGORIES

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS,\
                              subject_areas_dict
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

    class Meta:
        db_table = 'scipost_vgm'

    def __str__(self):
        return 'From %s to %s' % (self.start_date.strftime('%Y-%m-%d'),
                                  self.end_date.strftime('%Y-%m-%d'))


class Feedback(models.Model):
    """
    Feedback, suggestion or criticism on any aspect of SciPost.
    """
    VGM = models.ForeignKey(VGM, blank=True, null=True)
    by = models.ForeignKey(Contributor)
    date = models.DateField()
    feedback = models.TextField()

    class Meta:
        db_table = 'scipost_feedback'

    def __str__(self):
        return '%s: %s' % (self.by, self.feedback[:50])

    def as_li(self):
        html = ('<div class="Feedback">'
                '<h3><em>by {{ by }}</em></h3>'
                '<p>{{ feedback|linebreaks }}</p>'
                '</div>')
        context = Context({
            'feedback': self.feedback,
            'by': '%s %s' % (self.by.user.first_name,
                             self.by.user.last_name)})
        template = Template(html)
        return template.render(context)


class Nomination(models.Model):
    """
    Nomination to an Editorial Fellowship.
    """
    VGM = models.ForeignKey(VGM, blank=True, null=True)
    by = models.ForeignKey(Contributor)
    date = models.DateField()
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default='physics', verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    webpage = models.URLField(default='')
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField(Contributor,
                                          related_name='in_agreement_with_nomination', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField(Contributor,
                                        related_name='in_notsure_with_nomination', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField(Contributor,
                                             related_name='in_disagreement_with_nomination',
                                             blank=True)
    voting_deadline = models.DateTimeField('voting deadline', default=timezone.now)
    accepted = models.NullBooleanField()

    class Meta:
        db_table = 'scipost_nomination'

    def __str__(self):
        return '%s %s (nominated by %s)' % (self.first_name,
                                            self.last_name,
                                            self.by)

    def as_li(self):
        html = ('<div class="Nomination" id="nomination_id{{ nomination_id }}" '
                'style="background-color: #eeeeee;">'
                '<div class="row">'
                '<div class="col-4">'
                '<h3><em> {{ name }}</em></h3>'
                '<p>Nominated by {{ proposer }}</p>'
                '</div>'
                '<div class="col-4">'
                '<p><a href="{{ webpage }}">Webpage</a></p>'
                '<p>Discipline: {{ discipline }}</p></div>'
                '<div class="col-4"><p>expertise:<ul>')
        for exp in self.expertises:
            html += '<li>%s</li>' % subject_areas_dict[exp]
        html += '</ul></div></div></div>'
        context = Context({
            'nomination_id': self.id,
            'proposer': '%s %s' % (self.by.user.first_name,
                                   self.by.user.last_name),
            'name': self.first_name + ' ' + self.last_name,
            'discipline': self.get_discipline_display(),
            'webpage': self.webpage,
        })
        template = Template(html)
        return template.render(context)

    def votes_as_ul(self):
        template = Template('''
        <ul class="opinionsDisplay">
        <li style="background-color: #000099">Agree {{ nr_A }}</li>
        <li style="background-color: #555555">Abstain {{ nr_N }}</li>
        <li style="background-color: #990000">Disagree {{ nr_D }}</li>
        </ul>
        ''')
        context = Context({'nr_A': self.nr_A, 'nr_N': self.nr_N, 'nr_D': self.nr_D})
        return template.render(context)

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
    VGM = models.ForeignKey(VGM, blank=True, null=True)
    background = models.TextField()
    motion = models.TextField()
    put_forward_by = models.ForeignKey(Contributor)
    date = models.DateField()
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField(Contributor,
                                          related_name='in_agreement_with_motion', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField(Contributor,
                                        related_name='in_notsure_with_motion', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField(Contributor,
                                             related_name='in_disagreement_with_motion',
                                             blank=True)
    voting_deadline = models.DateTimeField('voting deadline', default=timezone.now)
    accepted = models.NullBooleanField()

    class Meta:
        db_table = 'scipost_motion'

    def __str__(self):
        return self.motion[:32]

    def as_li(self):
        html = ('<div class="Motion" id="motion_id{{ motion_id }}">'
                '<h3><em>Motion {{ motion_id }}, put forward by {{ proposer }}</em></h3>'
                '<h3>Background:</h3><p>{{ background|linebreaks }}</p>'
                '<h3>Motion:</h3>'
                '<div class="flex-container"><div class="flex-greybox">'
                '<p style="background-color: #eeeeee;">{{ motion|linebreaks }}</p>'
                '</div></div>'
                '</div>')
        context = Context({
            'motion_id': self.id,
            'proposer': '%s %s' % (self.put_forward_by.user.first_name,
                                   self.put_forward_by.user.last_name),
            'background': self.background,
            'motion': self.motion, })
        template = Template(html)
        return template.render(context)

    def votes_as_ul(self):
        template = Template('''
        <ul class="opinionsDisplay">
        <li style="background-color: #000099">Agree {{ nr_A }}</li>
        <li style="background-color: #555555">Abstain {{ nr_N }}</li>
        <li style="background-color: #990000">Disagree {{ nr_D }}</li>
        </ul>
        ''')
        context = Context({'nr_A': self.nr_A, 'nr_N': self.nr_N, 'nr_D': self.nr_D})
        return template.render(context)

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
