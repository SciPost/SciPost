__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404

from scipost.behaviors import orcid_validator
from scipost.constants import (
    TITLE_CHOICES, SCIPOST_DISCIPLINES, DISCIPLINE_PHYSICS, SCIPOST_SUBJECT_AREAS)
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor

from comments.models import Comment
from journals.models import Publication, PublicationAuthorsTable
from ontology.models import Topic
from theses.models import ThesisLink

from .constants import PROFILE_NON_DUPLICATE_REASONS
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
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default=DISCIPLINE_PHYSICS, verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id",
                                blank=True, validators=[orcid_validator])
    webpage = models.URLField(blank=True)

    # Topics for semantic linking
    topics = models.ManyToManyField('ontology.Topic', blank=True)

    # Preferences for interactions with SciPost:
    accepts_SciPost_emails = models.BooleanField(default=True)
    accepts_refereeing_requests = models.BooleanField(default=True)

    objects = ProfileQuerySet.as_manager()

    class Meta:
        ordering = ['last_name']

    def __str__(self):
        return '%s, %s %s' % (self.last_name, self.get_title_display(), self.first_name)

    @property
    def email(self):
        return getattr(self.emails.filter(primary=True).first(), 'email', '')

    @property
    def has_contributor(self):
        has_contributor = False
        try:
            has_contributor = (self.contributor is not None)
        except Contributor.DoesNotExist:
            pass
        return has_contributor

    def get_absolute_url(self):
        return reverse('profiles:profile_detail', kwargs={'pk': self.id})

    def publications(self):
        """
        Returns all the publications associated to this Profile.
        """
        return Publication.objects.published().filter(
            models.Q(authors__unregistered_author__profile=self) |
            models.Q(authors__contributor__profile=self))

    def comments(self):
        """
        Returns all the Comments associated to this Profile.
        """
        return Comment.objects.filter(author__profile=self)

    def theses(self):
        """
        Returns all the Theses associated to this Profile.
        """
        return ThesisLink.objects.filter(author_as_cont__profile=self)


class ProfileEmail(models.Model):
    """Any email related to a Profile instance."""
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    email = models.EmailField()
    still_valid = models.BooleanField(default=True)
    primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ['profile', 'email']
        ordering = ['-primary', '-still_valid', 'email']
        default_related_name = 'emails'

    def __str__(self):
        return self.email


def get_profiles(slug):
    """
    Returns a list of Profiles for which there exists at least one
    Publication/Submission object carrying this Topic.
    """
    topic = get_object_or_404(Topic, slug=slug)
    publications = PublicationAuthorsTable.objects.filter(publication__topics__in=[topic,])
    cont_id_list = [tbl.contributor.id for tbl in publications.all() \
                    if tbl.contributor is not None]
    unreg_id_list = [tbl.unregistered_author.id for tbl in publications.all() \
                     if tbl.unregistered_author is not None]
    print (unreg_id_list)
    return Profile.objects.filter(models.Q(contributor__id__in=cont_id_list) |
                                  models.Q(unregisteredauthor__id__in=unreg_id_list))


class ProfileNonDuplicates(models.Model):
    """
    Sets of Profiles which are not duplicates of each other,
    and thus can be filtered out of any dynamically generated list of potential duplicates.
    """
    profiles = models.ManyToManyField('profiles.Profile')
    reason = models.CharField(max_length=32, choices=PROFILE_NON_DUPLICATE_REASONS)

    class Meta:
        verbose_name = 'Profile non-duplicates'
        verbose_name_plural = 'Profile non-duplicates'

    def __str__(self):
        return '%s, %s (%i)' % (self.profiles.first().last_name,
                                self.profiles.first().first_name,
                                self.profiles.count())

    @property
    def full_name(self):
        return '%s%s' % (self.profiles.first().last_name, self.profiles.first().first_name)
