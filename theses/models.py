__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.utils import timezone

from journals.constants import SCIPOST_JOURNALS_DOMAINS
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS

from .constants import THESIS_TYPES
from .managers import ThesisLinkManager


class ThesisLink(models.Model):
    """ An URL pointing to a thesis """
    requested_by = models.ForeignKey(
        'scipost.Contributor', blank=True, null=True,
        related_name='requested_theses',
        on_delete=models.CASCADE)
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey(
        'scipost.Contributor', blank=True, null=True,
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
        'scipost.Contributor', blank=True,
        related_name='theses')
    author_claims = models.ManyToManyField(
        'scipost.Contributor', blank=True,
        related_name='claimed_theses')
    author_false_claims = models.ManyToManyField(
        'scipost.Contributor', blank=True,
        related_name='false_claimed_theses')
    supervisor = models.CharField(max_length=1000)
    supervisor_as_cont = models.ManyToManyField(
        'scipost.Contributor', blank=True,
        verbose_name='supervisor(s)',
        related_name='supervised_theses')
    institution = models.CharField(
        max_length=300,
        verbose_name='degree granting institution')
    defense_date = models.DateField(verbose_name='date of thesis defense')
    abstract = models.TextField(verbose_name='abstract, outline or summary')
    latest_activity = models.DateTimeField(default=timezone.now)

    # Comments can be added to a ThesisLink
    comments = GenericRelation('comments.Comment', related_query_name='theses')

    objects = ThesisLinkManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('theses:thesis', args=[self.id])
