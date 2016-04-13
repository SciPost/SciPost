from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import JSONField
from django.template import Template, Context

from django_countries.fields import CountryField

from mptt.models import MPTTModel, TreeForeignKey

from .models import *

SCIPOST_DISCIPLINES = (
    ('physics', 'Physics'),
    )
disciplines_dict = dict(SCIPOST_DISCIPLINES)

PHYSICS_SPECIALIZATIONS = (
    ('A', 'Atomic, Molecular and Optical Physics'),
    ('B', 'Biophysics'),
    ('C', 'Condensed Matter Physics'),
    ('F', 'Fluid Dynamics'),
    ('G', 'Gravitation, Cosmology and Astroparticle Physics'),
    ('H', 'High-Energy Physics'),
    ('M', 'Mathematical Physics'),
    ('N', 'Nuclear Physics'),
    ('Q', 'Quantum Statistical Mechanics'),
    ('S', 'Statistical and Soft Matter Physics'),
    )
physics_specializations = dict(PHYSICS_SPECIALIZATIONS)


CONTRIBUTOR_STATUS = (
    # status determine the type of Contributor:
    # 0: newly registered (unverified; not allowed to submit, comment or vote)
    # 1: contributor has been vetted through
    #
    # Negative status denotes rejected requests or:
    # -1: not a professional scientist (defined as at least PhD student in known university)
    # -2: other account already exists for this person
    # -3: barred from SciPost (abusive behaviour)
    # -4: disabled account (deceased)
    (0, 'newly registered'),
    (1, 'normal user'),
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
    invitation_key = models.CharField(max_length=40, default='', blank=True, null=True)
    activation_key = models.CharField(max_length=40, default='')
    key_expires = models.DateTimeField(default=timezone.now)
    status = models.SmallIntegerField(default=0, choices=CONTRIBUTOR_STATUS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    specializations = JSONField(default={})
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id", blank=True)
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, verbose_name="address", default='', blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page', blank=True)
    vetted_by = models.ForeignKey('self', related_name="contrib_vetted_by", blank=True, null=True)


    def __str__ (self):
        return self.user.last_name + ', ' + self.user.first_name


    def private_info_as_table (self):
        template = Template('''
        <table>
        <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
        <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
        <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
        <tr><td>Email: </td><td>&nbsp;</td><td>{{ email }}</td></tr>
        <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
        <tr><td>Country of employment: </td><td>&nbsp;</td><td>{{ country_of_employment }}</td></tr>
        <tr><td>Affiliation: </td><td>&nbsp;</td><td>{{ affiliation }}</td></tr>
        <tr><td>Address: </td><td>&nbsp;</td><td>{{ address }}</td></tr>
        <tr><td>Personal web page: </td><td>&nbsp;</td><td>{{ personalwebpage }}</td></tr>
        </table>
        ''')
        context = Context({
                'title': title_dict[self.title],
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'orcid_id': self.orcid_id,
                'country_of_employment': str(self.country_of_employment.name),
                'affiliation': self.affiliation,
                'address': self.address,
                'personalwebpage': self.personalwebpage
                })
        return template.render(context)


    def public_info_as_table (self):
        template = Template('''
        <table>
        <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
        <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
        <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
        <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
        <tr><td>Country of employment: </td><td>&nbsp;</td><td>{{ country_of_employment }}</td></tr>
        <tr><td>Affiliation: </td><td>&nbsp;</td><td>{{ affiliation }}</td></tr>
        <tr><td>Personal web page: </td><td>&nbsp;</td><td>{{ personalwebpage }}</td></tr>
        </table>
        ''')
        context = Context({
                'title': title_dict[self.title],
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'orcid_id': self.orcid_id,
                'country_of_employment': str(self.country_of_employment.name),
                'affiliation': self.affiliation,
                'address': self.address,
                'personalwebpage': self.personalwebpage
                })
        return template.render(context)



##################
## Invitations ###
##################

INVITATION_TYPE = (
    ('F', 'Editorial Fellow'),
    ('C', 'Contributor'),
    ('R', 'Refereeing'),
    )

INVITATION_STYLE = (
    ('F', 'formal'),
    ('P', 'personal'),
    )

class RegistrationInvitation(models.Model):
    """ 
    Invitation to particular persons for registration
    """
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email_address = models.EmailField()
    invitation_type = models.CharField(max_length=2, choices=INVITATION_TYPE, default='C')
    message_style = models.CharField(max_length=1, choices=INVITATION_STYLE, default='F')
    personal_message = models.TextField(blank=True, null=True)
    invitation_key = models.CharField(max_length=40, default='')
    key_expires = models.DateTimeField(default=timezone.now)
    date_sent = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey(Contributor, blank=True, null=True)
    responded = models.BooleanField(default=False)

    def __str__ (self):
        return self.invitation_type + ' ' + self.first_name + ' ' + self.last_name + ' on ' + self.date_sent.strftime("%Y-%m-%d")



AUTHORSHIP_CLAIM_STATUS = (
    (1, 'accepted'),
    (0, 'not yet vetted (pending)'),
    (-1, 'rejected'),
)

class AuthorshipClaim(models.Model):
    claimant = models.ForeignKey(Contributor, related_name='claimant')
    submission = models.ForeignKey('submissions.Submission', blank=True, null=True)
    commentary = models.ForeignKey('commentaries.Commentary', blank=True, null=True)
    thesislink = models.ForeignKey('theses.ThesisLink', blank=True, null=True)
    vetted_by = models.ForeignKey (Contributor, blank=True, null=True)
    status = models.SmallIntegerField(choices=AUTHORSHIP_CLAIM_STATUS, default=0)
    


#######################
### Assessments objects
#######################


### Assessments

#ASSESSMENT_CHOICES = (
#    (101, '-'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
#    (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')
#    )

#class Assessment(models.Model):
#    """ 
#    Base class for all assessments.
#    """
#    rater = models.ForeignKey(Contributor)
#    submission = models.ForeignKey('submissions.Submission', blank=True, null=True)
#    comment = models.ForeignKey('comments.Comment', blank=True, null=True)
#    relevance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    importance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    clarity = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    validity = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    rigour = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    originality = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)
#    significance = models.PositiveSmallIntegerField(choices=ASSESSMENT_CHOICES, default=101)


### Opinions

#OPINION_CHOICES = (
#    ('ABS', '-'),
#    ('A', 'agree'),
#    ('N', 'not sure'),
#    ('D', 'disagree'),
#)
#opinion_choices_dict = dict(OPINION_CHOICES)

#class Opinion(models.Model):
#    rater = models.ForeignKey(Contributor)
#    comment = models.ForeignKey('comments.Comment')
#    opinion = models.CharField(max_length=3, choices=OPINION_CHOICES, default='ABS')


### AssessmentAggregates

#class AssessmentAggregate(models.Model):
#    """
#    Aggregated assessments for an object.
#    """
#    nr = models.PositiveSmallIntegerField(default=0)
#    nr_relevance_ratings = models.IntegerField(default=0)
#    relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_importance_ratings = models.IntegerField(default=0)
#    importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_clarity_ratings = models.IntegerField(default=0)
#    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_validity_ratings = models.IntegerField(default=0)
#    validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_rigour_ratings = models.IntegerField(default=0)
#    rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_originality_ratings = models.IntegerField(default=0)
#    originality_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
#    nr_significance_ratings = models.IntegerField(default=0)
#    significance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)



#########
# Teams #
#########

class Team(models.Model):
    """
    Team of Contributors, to enable private collaborations.
    """
    leader = models.ForeignKey(Contributor)
    members = models.ManyToManyField (Contributor, blank=True, related_name='team_members')
    name = models.CharField(max_length=20)

    def __str__(self):
        return name + ' (led by ' + leader.user.first_name + ' ' + leader.user.last_name + ')'
    

#########
# Lists #
#########

class Node(MPTTModel):
    """
    Node of a list (tree of submissions, commentaries, thesislinks). 
    Requires django-mptt.
    """
    owner = models.ForeignKey(Team)
    name = models.CharField(max_length=100)
    private = models.BooleanField(default=True)
    parent = TreeForeignKey('self', blank=True, null=True, related_name='children', db_index=True)
    description = models.TextField(blank=True, null=True)
    submissions = models.ManyToManyField('submissions.Submission', blank=True, related_name='node_submissions')
    commentaries = models.ManyToManyField('commentaries.Commentary', blank=True, related_name='node_commentaries')
    thesislinks = models.ManyToManyField('theses.ThesisLink', blank=True, related_name='node_thesislinks')
    annotation = models.TextField(blank=True, null=True)

    
