__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from scipost.behaviors import orcid_validator
from scipost.constants import (
    TITLE_CHOICES, SCIPOST_DISCIPLINES, DISCIPLINE_PHYSICS, SCIPOST_SUBJECT_AREAS)
from scipost.fields import ChoiceArrayField

from .managers import ProfileQuerySet


class Profile(models.Model):
    """
    A Profile object instance contains information about an individual.

    This individual is a potential SciPost Contributor but is not necessarily registered.
    It is created and used by Admin, EdAdmin or other internal SciPost staff.

    For registered Contributors, a profile is initially created from the contributor-filled
    information in the Contributor object. Profile should thus be viewed as containing
    the Admin-certified version of this information.

    The information is only partial, and is meant to be used among others to:

    #. help with editorial matters:
       #. help EdAdmin identify prospective Fellows
       #. help Fellows identify appropriate referees
       #. mark potential conflicts of interest

    #. allow respecting people's preferences:
       #. mark somebody as not willing to receive emails from SciPost.
       #. mark somebody as a non-referee (if that person does not want to referee for SciPost)
    """

    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default=DISCIPLINE_PHYSICS, verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id",
                                blank=True, validators=[orcid_validator])
    webpage = models.URLField(blank=True)
    # Preferences for interactions with SciPost:
    accepts_SciPost_emails = models.BooleanField(default=True)
    accepts_refereeing_requests = models.BooleanField(default=True)

    objects = ProfileQuerySet.as_manager()

    class Meta:
        ordering = ['last_name']

    def __str__(self):
        return '%s, %s %s' % (self.last_name, self.get_title_display(), self.first_name)


class AlternativeEmail(models.Model):
    """
    It is often the case that somebody has multiple email addresses.
    The 'email' field of a given Profile, Contributor or other person-based object
    is then interpreted as representing the current address.
    An AlternativeEmail is bound to a Profile and holds info on eventual
    secondary email addresses.
    """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    email = models.EmailField()
    still_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = ['profile', 'email']
