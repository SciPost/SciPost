__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from .managers import PetitionSignatoryQuerySet

from scipost.constants import TITLE_CHOICES


class Petition(models.Model):
    title = models.CharField(max_length=256)
    slug = models.SlugField()
    headline = models.CharField(max_length=256)
    preamble = models.TextField(blank=True, null=True)
    statement = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("petitions:petition", kwargs={"slug": self.slug})


class PetitionSignatory(models.Model):
    petition = models.ForeignKey("petitions.Petition", on_delete=models.CASCADE)
    signatory = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE, blank=True, null=True
    )
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email = models.EmailField()
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name="affiliation")
    organization = models.ForeignKey(
        "organizations.Organization", blank=True, null=True, on_delete=models.SET_NULL
    )
    signed_on = models.DateTimeField(auto_now_add=True)
    verification_key = models.CharField(max_length=40, blank=True)
    verified = models.BooleanField(default=False)

    objects = PetitionSignatoryQuerySet.as_manager()

    class Meta:
        default_related_name = "petition_signatories"
        ordering = ["last_name", "country_of_employment", "affiliation"]
        verbose_name_plural = "petition signatories"

    def __str__(self):
        return "%s, %s %s (%s)" % (
            self.last_name,
            self.get_title_display(),
            self.first_name,
            self.petition.slug,
        )
