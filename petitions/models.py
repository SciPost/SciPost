from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from scipost.constants import TITLE_CHOICES



class Petition(models.Model):
    title = models.CharField(max_length=256)
    slug = models.SlugField()
    headline = models.CharField(max_length=256)
    statement = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PetitionSignatory(models.Model):
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE)
    signatory = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                  blank=True, null=True)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email = models.EmailField()
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    signed_on = models.DateTimeField(auto_now_add=True)
    verification_key = models.CharField(max_length=40, blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'petition signatories'

    def __str__(self):
        return '%s, %s %s (%s)' % (self.last_name, self.get_title_display(),
                                   self.first_name, self.petition.slug)
