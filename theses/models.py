from django.utils import timezone
from django.db import models

from journals.models import SCIPOST_JOURNALS_DOMAINS
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor

from .managers import ThesisLinkManager


class ThesisLink(models.Model):
    MASTER_THESIS = 'MA'
    PHD_THESIS = 'PhD'
    HABILITATION_THESIS = 'Hab'
    THESIS_TYPES = (
        (MASTER_THESIS, 'Master\'s'),
        (PHD_THESIS, 'Ph.D.'),
        (HABILITATION_THESIS, 'Habilitation'),
    )
    THESIS_TYPES_DICT = dict(THESIS_TYPES)

    """ An URL pointing to a thesis """
    requested_by = models.ForeignKey(
        Contributor, blank=True, null=True,
        related_name='thesislink_requested_by',
        on_delete=models.CASCADE)
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey(
        Contributor, blank=True, null=True,
        on_delete=models.CASCADE)
    type = models.CharField(choices=THESIS_TYPES, max_length=3)
    discipline = models.CharField(
        max_length=20, choices=SCIPOST_DISCIPLINES,
        default='physics')
    domain = models.CharField(
        max_length=3, choices=SCIPOST_JOURNALS_DOMAINS,
        blank=False)
    subject_area = models.CharField(
        max_length=10,
        choices=SCIPOST_SUBJECT_AREAS,
        default='Phys:QP')
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300, verbose_name='title')
    pub_link = models.URLField(verbose_name='URL (external repository)')
    author = models.CharField(max_length=1000)
    author_as_cont = models.ManyToManyField(
        Contributor, blank=True,
        related_name='author_cont')
    author_claims = models.ManyToManyField(
        Contributor, blank=True,
        related_name='authors_thesis_claims')
    author_false_claims = models.ManyToManyField(
        Contributor, blank=True,
        related_name='authors_thesis_false_claims')
    supervisor = models.CharField(max_length=1000, default='')
    supervisor_as_cont = models.ManyToManyField(
        Contributor, blank=True,
        verbose_name='supervisor(s)',
        related_name='supervisor_cont')
    institution = models.CharField(
        max_length=300,
        verbose_name='degree granting institution')
    defense_date = models.DateField(verbose_name='date of thesis defense')
    abstract = models.TextField(verbose_name='abstract, outline or summary')
    latest_activity = models.DateTimeField(default=timezone.now)

    objects = ThesisLinkManager()

    def __str__(self):
        return self.title
