from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from django_countries.fields import CountryField

from .models import *

SCIPOST_DISCIPLINES = (
    ('physics', 'Physics'),
    )
disciplines_dict = dict(SCIPOST_DISCIPLINES)



CONTRIBUTOR_RANKS = (
    # ranks determine the type of Contributor:
    # 0: newly registered (unverified; not allowed to submit, comment or vote)
    # 1: normal user (allowed to submit, comment and vote)
    # 2: scipost editor (1 + no need for vetting of comments, also allowed to vet commentary request and comments from normal users)
    # 3: scipost journal editor (2 + allowed to accept papers in SciPost Journals)
    # 4: scipost journal editor-in-chief 
    # 5: Lead Editor (all rights granted, including rank promotions and overriding all)
    #
    # Negative ranks denote rejected requests or :
    # -1: not a professional scientist (defined as at least PhD student in known university)
    # -2: other account already exists for this person
    # -3: barred from SciPost (abusive behaviour)
    # -4: disabled account (deceased)
    (0, 'newly registered'),
    (1, 'normal user'),
    (2, 'Commentary Editor'),
    (3, 'Journal Specialty Editor'),
    (4, 'Journal Editor-in-chief'),
    (5, 'Field Head Editor'),
    (-1, 'not a professional scientist'),
    (-2, 'other account already exists'),
    (-3, 'barred from SciPost'),
    (-4, 'account disabled'),
    )

TITLE_CHOICES = (
    ('PR', 'Prof.'),
    ('DR', 'Dr'),
    ('MR', 'Mr'),
    ('MRS', 'Mrs'),
    )
title_dict = dict(TITLE_CHOICES)


class Contributor(models.Model):
    """ All users of SciPost are Contributors. Permissions determine the sub-types. """
    user = models.OneToOneField(User)
    # username, password, email, first_name and last_name are inherited from User
    activation_key = models.CharField(max_length=40, default='')
    key_expires = models.DateTimeField(default=timezone.now)
    rank = models.SmallIntegerField(default=0, choices=CONTRIBUTOR_RANKS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id", blank=True)
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, verbose_name="address", default='', blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page', blank=True)
    #vetted_by = models.OneToOneField(Contributor, related_name='vetted_by') TO ACTIVATE


    def __str__ (self):
        return self.user.last_name + ', ' + self.user.first_name

    def as_table (self):
        output = '<table>'
        output += '<tr><td>Title: </td><td>&nbsp;</td><td>' + title_dict[self.title] + '</td></tr>'
        output += '<tr><td>First name: </td><td>&nbsp;</td><td>' + self.user.first_name + '</td></tr>'
        output += '<tr><td>Last name: </td><td>&nbsp;</td><td>' + self.user.last_name + '</td></tr>'
        output += '<tr><td>Email: </td><td>&nbsp;</td><td>' + self.user.email + '</td></tr>'
        output += '<tr><td>ORCID id: </td><td>&nbsp;</td><td>' + self.orcid_id + '</td></tr>'
        output += '<tr><td>Country of employment: </td><td>&nbsp;</td><td>' + str(self.country_of_employment.name) + '</td></tr>'
        output += '<tr><td>Affiliation: </td><td>&nbsp;</td><td>' + self.affiliation + '</td></tr>'
        output += '<tr><td>Address: </td><td>&nbsp;</td><td>' + self.address + '</td></tr>'
        output += '<tr><td>Personal web page: </td><td>&nbsp;</td><td>' + self.personalwebpage + '</td></tr>'
        output += '</table>'
        return output



#######################
### Assessments objects
#######################


### Assessments

ASSESSMENT_CHOICES = (
    (101, '-'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
    (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')
    )

class Assessment(models.Model):
    """ 
    Base class for all assessments.
    """
    rater = models.ForeignKey(Contributor)
    submission = models.ForeignKey('submissions.Submission', blank=True, null=True)
    comment = models.ForeignKey('comments.Comment', blank=True, null=True)
    relevance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    importance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    clarity = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    validity = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    rigour = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    originality = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
    significance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)


### AssessmentAggregates

class AssessmentAggregate(models.Model):
    """
    Aggregated assessments for an object.
    """
    nr = models.PositiveSmallIntegerField(default=0)
    nr_relevance_ratings = models.IntegerField(default=0)
    relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_importance_ratings = models.IntegerField(default=0)
    importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_clarity_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_validity_ratings = models.IntegerField(default=0)
    validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_rigour_ratings = models.IntegerField(default=0)
    rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_originality_ratings = models.IntegerField(default=0)
    originality_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_significance_ratings = models.IntegerField(default=0)
    significance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

