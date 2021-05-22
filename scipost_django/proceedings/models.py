__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.db import models
from django.utils import timezone

from scipost.behaviors import TimeStampedModel

from .managers import ProceedingsQuerySet

today = timezone.now().date()


class Proceedings(TimeStampedModel):
    """
    A Proceeding is a special kind of Journal Issue.
    """
    # Link to the actual Journal platform
    issue = models.OneToOneField(
        'journals.Issue', on_delete=models.CASCADE, related_name='proceedings',
        limit_choices_to=models.Q(in_volume__in_journal__doi_label='SciPostPhysProc') | models.Q(in_journal__doi_label='SciPostPhysProc'))
    minimum_referees = models.PositiveSmallIntegerField(
        help_text='Require an explicit minimum number of referees for the default ref cycle.',
        blank=True, null=True)

    # Event the Proceedings is for
    event_name = models.CharField(max_length=256, blank=True)
    event_suffix = models.CharField(max_length=256, blank=True)
    event_description = models.TextField(blank=True)
    event_start_date = models.DateField(null=True, blank=True)
    event_end_date = models.DateField(null=True, blank=True)
    logo = models.ImageField(upload_to='proceedings/images/', blank=True)
    picture = models.ImageField(upload_to='proceedings/images/', blank=True)
    picture_credit = models.CharField(max_length=512, blank=True)
    cover_image = models.ImageField(upload_to='proceedings/images/', blank=True)

    # Fellows
    lead_fellow = models.ForeignKey('colleges.Fellowship', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    fellowships = models.ManyToManyField('colleges.Fellowship', blank=True)

    # Submission data
    submissions_open = models.DateField()
    submissions_deadline = models.DateField()
    submissions_close = models.DateField()

    # Templates
    template_latex_tgz = models.FileField(
        verbose_name='Template (LaTeX, gzipped tarball)',
        help_text='Gzipped tarball of the LaTeX template package',
        upload_to='UPLOADS/TEMPLATES/latex/%Y/', max_length=256, blank=True)

    objects = ProceedingsQuerySet.as_manager()

    class Meta:
        verbose_name = 'Proceedings'
        verbose_name_plural = 'Proceedings'
        default_related_name = 'proceedings'

    def __str__(self):
        _str = self.event_name
        if self.event_suffix:
            _str += ' ({s})'.format(s=self.event_suffix)
        return _str

    def get_absolute_url(self):
        return reverse('proceedings:proceedings_details', args=(self.id,))

    @property
    def open_for_submission(self):
        return self.submissions_open <= today and self.submissions_close >= today
