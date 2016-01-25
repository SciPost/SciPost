from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from django_countries.fields import CountryField

from .models import *


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
    activation_key = models.CharField(max_length=40, default='')
    key_expires = models.DateTimeField(default=timezone.now)
    rank = models.SmallIntegerField(default=0, choices=CONTRIBUTOR_RANKS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    # username, password, email, first_name and last_name are inherited from User
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id", blank=True)
    #nationality = CountryField(blank=True)
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, verbose_name="address", default='', blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page', blank=True)
    #vetted_by = models.OneToOneField(Contributor, related_name='vetted_by') TO ACTIVATE

    # permissions
    can_vet_reg_req = models.BooleanField(default=False, verbose_name='can vet registration requests')
    can_vet_commentary_req = models.BooleanField(default=False, verbose_name='can vet commentary page requests')
    can_process_incoming_submissions = models.BooleanField(default=False, verbose_name='can process incoming submissions')
    can_vet_comments = models.BooleanField(default=False, verbose_name='can vet submitted comments')
    can_vet_author_replies = models.BooleanField(default=False, verbose_name='can vet submitted author replies')
    can_vet_reports = models.BooleanField(default=False, verbose_name='can vet submitted reports')

    nr_comments = models.PositiveSmallIntegerField(default=0)
    nr_comment_relevance_ratings = models.IntegerField(default=0)
    comment_relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_comment_importance_ratings = models.IntegerField(default=0)
    comment_importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_comment_clarity_ratings = models.IntegerField(default=0)
    comment_clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_comment_validity_ratings = models.IntegerField(default=0)
    comment_validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_comment_rigour_ratings = models.IntegerField(default=0)
    comment_rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    nr_authorreplies = models.PositiveSmallIntegerField(default=0)
    nr_authorreply_relevance_ratings = models.IntegerField(default=0)
    authorreply_relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_authorreply_importance_ratings = models.IntegerField(default=0)
    authorreply_importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_authorreply_clarity_ratings = models.IntegerField(default=0)
    authorreply_clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_authorreply_validity_ratings = models.IntegerField(default=0)
    authorreply_validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_authorreply_rigour_ratings = models.IntegerField(default=0)
    authorreply_rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    nr_reports = models.PositiveSmallIntegerField(default=0)
    nr_report_relevance_ratings = models.IntegerField(default=0)
    report_relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_report_importance_ratings = models.IntegerField(default=0)
    report_importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_report_clarity_ratings = models.IntegerField(default=0)
    report_clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_report_validity_ratings = models.IntegerField(default=0)
    report_validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_report_rigour_ratings = models.IntegerField(default=0)
    report_rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    def __str__ (self):
        return self.user.username

    def as_table (self):
        output = '<table>'
        output += '<tr><td>Title: </td><td>&nbsp;</td><td>' + title_dict[self.title] + '</td></tr>'
        output += '<tr><td>First name: </td><td>&nbsp;</td><td>' + self.user.first_name + '</td></tr>'
        output += '<tr><td>Last name: </td><td>&nbsp;</td><td>' + self.user.last_name + '</td></tr>'
        output += '<tr><td>Email: </td><td>&nbsp;</td><td>' + self.user.email + '</td></tr>'
        output += '<tr><td>ORCID id: </td><td>&nbsp;</td><td>' + self.orcid_id + '</td></tr>'
        #output += '<tr><td>Nationality: </td><td>&nbsp;</td><td>' + str(self.nationality.name) + '</td></tr>'
        output += '<tr><td>Country of employment: </td><td>&nbsp;</td><td>' + str(self.country_of_employment.name) + '</td></tr>'
        output += '<tr><td>Affiliation: </td><td>&nbsp;</td><td>' + self.affiliation + '</td></tr>'
        output += '<tr><td>Address: </td><td>&nbsp;</td><td>' + self.address + '</td></tr>'
        output += '<tr><td>Personal web page: </td><td>&nbsp;</td><td>' + self.personalwebpage + '</td></tr>'
        output += '</table>'
        return output

    def permissions_as_table (self):
        output = '<table>'
        if self.can_vet_reg_req:
            output += '<tr><td>Can vet registration requests</td></tr>'
        if self.can_vet_commentary_req:
            output += '<tr><td>Can vet commentary page requests</td></tr>'
        if self.can_process_incoming_submissions:
            output += '<tr><td>Can process incoming submissions</td></tr>'
        if self.can_vet_comments:
            output += '<tr><td>Can vet submitted comments</td></tr>'
        if self.can_vet_author_replies:
            output += '<tr><td>Can vet submitted author replies</td></tr>'
        if self.can_vet_reports:
            output += '<tr><td>Can vet submitted reports</td></tr>'
        output += '</table>'
        return output


#class LeadEditorGroup(models.Group)
