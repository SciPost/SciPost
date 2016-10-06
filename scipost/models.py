import datetime 

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_countries.fields import CountryField

from .models import *


SCIPOST_DISCIPLINES = (
    ('physics', 'Physics'),
    ('astrophysics', 'Astrophysics'),
    ('mathematics', 'Mathematics'),
    ('computerscience', 'Computer Science'),
    )
disciplines_dict = dict(SCIPOST_DISCIPLINES)

SCIPOST_SUBJECT_AREAS = (
    ('Physics', (
        ('Phys:AE', 'Atomic, Molecular and Optical Physics - Experiment'),
        ('Phys:AT', 'Atomic, Molecular and Optical Physics - Theory'),
        ('Phys:BI', 'Biophysics'),
        ('Phys:CE', 'Condensed Matter Physics - Experiment'),
        ('Phys:CT', 'Condensed Matter Physics - Theory'),
        ('Phys:FD', 'Fluid Dynamics'),
        ('Phys:GR', 'Gravitation, Cosmology and Astroparticle Physics'),
        ('Phys:HE', 'High-Energy Physics - Experiment'),
        ('Phys:HT', 'High-Energy Physics- Theory'),
        ('Phys:HP', 'High-Energy Physics - Phenomenology'),
        ('Phys:MP', 'Mathematical Physics'),
        ('Phys:NE', 'Nuclear Physics - Experiment'),
        ('Phys:NT', 'Nuclear Physics - Theory'),
        ('Phys:QP', 'Quantum Physics'),
        ('Phys:SM', 'Statistical and Soft Matter Physics'),
        )
     ),
    ('Astrophysics', (
        ('Astro:GA', 'Astrophysics of Galaxies'),
        ('Astro:CO', 'Cosmology and Nongalactic Astrophysics'),
        ('Astro:EP', 'Earth and Planetary Astrophysics'),
        ('Astro:HE', 'High Energy Astrophysical Phenomena'),
        ('Astro:IM', 'Instrumentation and Methods for Astrophysics'),
        ('Astro:SR', 'Solar and Stellar Astrophysics'),
        )
     ),
    ('Mathematics', (
        ('Math:AG', 'Algebraic Geometry'),
        ('Math:AT', 'Algebraic Topology'),
        ('Math:AP', 'Analysis of PDEs'),
        ('Math:CT', 'Category Theory'),
        ('Math:CA', 'Classical Analysis and ODEs'),
        ('Math:CO', 'Combinatorics'),
        ('Math:AC', 'Commutative Algebra'),
        ('Math:CV', 'Complex Variables'),
        ('Math:DG', 'Differential Geometry'),
        ('Math:DS', 'Dynamical Systems'),
        ('Math:FA', 'Functional Analysis'),
        ('Math:GM', 'General Mathematics'),
        ('Math:GN', 'General Topology'), 
        ('Math:GT', 'Geometric Topology'),
        ('Math:GR', 'Group Theory'),
        ('Math:HO', 'History and Overview'),
        ('Math:IT', 'Information Theory'),
        ('Math:KT', 'K-Theory and Homology'),
        ('Math:LO', 'Logic'),
        ('Math:MP', 'Mathematical Physics'),
        ('Math:MG', 'Metric Geometry'),
        ('Math:NT', 'Number Theory'),
        ('Math:NA', 'Numerical Analysis'),
        ('Math:OA', 'Operator Algebras'),
        ('Math:OC', 'Optimization and Control'),
        ('Math:PR', 'Probability'),
        ('Math:QA', 'Quantum Algebra'),
        ('Math:RT', 'Representation Theory'),
        ('Math:RA', 'Rings and Algebras'),
        ('Math:SP', 'Spectral Theory'),
        ('Math:ST', 'Statistics Theory'),
        ('Math:SG', 'Symplectic Geometry'),
        )
     ),
    ('Computer Science', (
        ('Comp:AI', 'Artificial Intelligence'),
        ('Comp:CC', 'Computational Complexity'),
        ('Comp:CE', 'Computational Engineering, Finance, and Science'),
        ('Comp:CG', 'Computational Geometry'),
        ('Comp:GT', 'Computer Science and Game Theory'),
        ('Comp:CV', 'Computer Vision and Pattern Recognition'),
        ('Comp:CY', 'Computers and Society'),
        ('Comp:CR', 'Cryptography and Security'),
        ('Comp:DS', 'Data Structures and Algorithms'),
        ('Comp:DB', 'Databases'),
        ('Comp:DL', 'Digital Libraries'),
        ('Comp:DM', 'Discrete Mathematics'),
        ('Comp:DC', 'Distributed, Parallel, and Cluster Computing'),
        ('Comp:ET', 'Emerging Technologies'),
        ('Comp:FL', 'Formal Languages and Automata Theory'),
        ('Comp:GL', 'General Literature'),
        ('Comp:GR', 'Graphics'),
        ('Comp:AR', 'Hardware Architecture'),
        ('Comp:HC', 'Human-Computer Interaction'),
        ('Comp:IR', 'Information Retrieval'),
        ('Comp:IT', 'Information Theory'),
        ('Comp:LG', 'Learning'),
        ('Comp:LO', 'Logic in Computer Science'),
        ('Comp:MS', 'Mathematical Software'),
        ('Comp:MA', 'Multiagent Systems'),
        ('Comp:MM', 'Multimedia'),
        ('Comp:NI', 'Networking and Internet Architecture'),
        ('Comp:NE', 'Neural and Evolutionary Computing'),
        ('Comp:NA', 'Numerical Analysis'),
        ('Comp:OS', 'Operating Systems'),
        ('Comp:OH', 'Other Computer Science'),
        ('Comp:PF', 'Performance'),
        ('Comp:PL', 'Programming Languages'),
        ('Comp:RO', 'Robotics'),
        ('Comp:SI', 'Social and Information Networks'),
        ('Comp:SE', 'Software Engineering'),
        ('Comp:SD', 'Sound'),
        ('Comp:SC', 'Symbolic Computation'),
        ('Comp:SY', 'Systems and Control'),
        )
     ),
)
subject_areas_raw_dict = dict(SCIPOST_SUBJECT_AREAS)
# We want a dict of the form {'Phys:AT': 'Atomic...', ...}
subject_areas_dict = {}
for k in subject_areas_raw_dict.keys():
    subject_areas_dict.update(dict(subject_areas_raw_dict[k]))


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.
    Uses Django 1.9's postgres ArrayField
    and a MultipleChoiceField for its formfield.
    """
 
    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.MultipleChoiceField,
            'widget': forms.CheckboxSelectMultiple,
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


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
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, 
                                  default='physics', verbose_name='Main discipline')
    expertises = ChoiceArrayField(models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS), 
                                  blank=True, null=True)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id", blank=True)
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, verbose_name="address", default='', blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page', blank=True)
    vetted_by = models.ForeignKey('self', related_name="contrib_vetted_by", 
                                  blank=True, null=True)  
    accepts_SciPost_emails = models.BooleanField(default=True, 
                                                 verbose_name="I accept to receive SciPost emails")

    def __str__ (self):
        return self.user.last_name + ', ' + self.user.first_name


    def is_currently_available(self):
        unav_periods = UnavailabilityPeriod.objects.filter(
            contributor=self)
        available = True
        today = datetime.date.today()
        for unav in unav_periods:
            if unav.start < today and unav.end > today:
                available = False
        return available


    def private_info_as_table (self):
        template = Template('''
        <table>
        <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
        <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
        <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
        <tr><td>Email: </td><td>&nbsp;</td><td>{{ email }}</td></tr>
        <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
        <tr><td>Country of employment: </td><td>&nbsp;</td>
        <td>{{ country_of_employment }}</td></tr>
        <tr><td>Affiliation: </td><td>&nbsp;</td><td>{{ affiliation }}</td></tr>
        <tr><td>Address: </td><td>&nbsp;</td><td>{{ address }}</td></tr>
        <tr><td>Personal web page: </td><td>&nbsp;</td><td>{{ personalwebpage }}</td></tr>
        <tr><td>Accept SciPost emails: </td><td>&nbsp;</td><td>{{ accepts_SciPost_emails }}</td></tr>
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
            'personalwebpage': self.personalwebpage,
            'accepts_SciPost_emails': self.accepts_SciPost_emails,
        })
        return template.render(context)


    def public_info_as_table (self):
        """
        Prints out all publicly-accessible info as a table.
        """
        template = Template('''
        <table>
        <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
        <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
        <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
        <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
        <tr><td>Country of employment: </td><td>&nbsp;</td>
        <td>{{ country_of_employment }}</td></tr>
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

    def discipline_as_string(self):
        return disciplines_dict[self.discipline]

    def expertises_as_ul(self):
        output = '<ul>'
        for exp in self.expertises:
            output += '<li>' + subject_areas_dict[exp] + '</li>'
        output += '</ul>'
        return mark_safe(output)

    def assignments_summary_as_td(self):
        assignments = self.editorialassignment_set.all()
        nr_ongoing = assignments.filter(accepted=True, completed=False).count()
        nr_last_12mo = assignments.filter(
            date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_accepted = assignments.filter(accepted=True).count()
        nr_accepted_last_12mo = assignments.filter(
            accepted=True, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_refused = assignments.filter(accepted=False).count()
        nr_refused_last_12mo = assignments.filter(
            accepted=False, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_ignored = assignments.filter(accepted=None).count()
        nr_ignored_last_12mo = assignments.filter(
            accepted=None, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_completed = assignments.filter(completed=True).count()
        nr_completed_last_12mo = assignments.filter(
            completed=True, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        
        context = Context({
            'nr_ongoing': nr_ongoing,
            'nr_total': assignments.count(),
            'nr_last_12mo': nr_last_12mo,
            'nr_accepted': nr_accepted, 
            'nr_accepted_last_12mo': nr_accepted_last_12mo,
            'nr_refused': nr_refused,
            'nr_refused_last_12mo': nr_refused_last_12mo,
            'nr_ignored': nr_ignored,
            'nr_ignored_last_12mo': nr_ignored_last_12mo,
            'nr_completed': nr_completed,
            'nr_completed_last_12mo': nr_completed_last_12mo,
        })
        output = '<td>'
        if self.expertises:
            for expertise in self.expertises:
                output += subject_areas_dict[expertise] + '<br/>'
        output += ('</td>'
                   '<td>{{ nr_ongoing }}</td>'
                   '<td>{{ nr_last_12mo }} / {{ nr_total }}</td>'
                   '<td>{{ nr_accepted_last_12mo }} / {{ nr_accepted }}</td>'
                   '<td>{{ nr_refused_last_12mo }} / {{ nr_refused }}</td>'
                   '<td>{{ nr_ignored_last_12mo }} / {{ nr_ignored }}</td>'
                   '<td>{{ nr_completed_last_12mo }} / {{ nr_completed }}</td>\n')
        template = Template(output)
        return template.render(context)


class UnavailabilityPeriod(models.Model):
    contributor = models.ForeignKey(Contributor)
    start = models.DateField()
    end = models.DateField()


class Remark(models.Model):
    contributor = models.ForeignKey(Contributor)
    recommendation = models.ForeignKey('submissions.EICRecommendation', blank=True, null=True)
    date = models.DateTimeField()
    remark = models.TextField()

    def __str__(self):
        return (title_dict[self.contributor.title] + ' ' 
                + self.contributor.user.first_name + ' '
                + self.contributor.user.last_name + ' on ' 
                + self.date.strftime("%Y-%m-%d"))

    def as_li(self):
        output = '<li>{{ by }}<p>{{ remark }}</p>'
        context = Context({'by': str(self),
                           'remark': self.remark})
        template = Template(output)
        return template.render(context)

        
##################
## Invitations ###
##################

INVITATION_TYPE = (
    ('F', 'Editorial Fellow'),
    ('C', 'Contributor'),
    ('R', 'Refereeing'),
    ('ci', 'cited in submission'),
    ('cp', 'cited in publication'),
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
    email = models.EmailField()
    invitation_type = models.CharField(max_length=2, choices=INVITATION_TYPE, default='C')
    cited_in_submission = models.ForeignKey('submissions.Submission', blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication', blank=True, null=True)
    message_style = models.CharField(max_length=1, choices=INVITATION_STYLE, default='F')
    personal_message = models.TextField(blank=True, null=True)
    invitation_key = models.CharField(max_length=40, default='')
    key_expires = models.DateTimeField(default=timezone.now)
    date_sent = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey(Contributor, blank=True, null=True)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    responded = models.BooleanField(default=False)

    def __str__ (self):
        return (self.invitation_type + ' ' + self.first_name + ' ' + self.last_name 
                + ' on ' + self.date_sent.strftime("%Y-%m-%d"))



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
#    (101, '-'), # Only values between 0 and 100 are kept, anything outside limits is discarded.
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


##########
# Emails #
##########

# class EmailedTo(models.Model):
#     """
#     An email address used for emailing.
#     An instance is created by a method as send_precooked_email
#     if the chosen message hasn't been sent to this address before.
#     Helps prevent multiple emailing with same message.
#     """
#     email = models.EmailField()


SCIPOST_FROM_ADDRESSES = (
    ('Admin', 'SciPost Admin <admin@scipost.org>'),
    ('J.-S. Caux', 'J.-S. Caux <jscaux@scipost.org>'),
    ('J. van Wezel', 'J. van Wezel <vanwezel@scipost.org>'),
)
SciPost_from_addresses_dict = dict(SCIPOST_FROM_ADDRESSES)


class PrecookedEmail(models.Model):
    """
    Each instance contains an email template in both plain and html formats.
    Can only be created by Admins.
    For further use in scipost:send_precooked_email method.
    """
    email_subject = models.CharField(max_length=300)
    email_text = models.TextField()
    email_text_html = models.TextField()
    date_created = models.DateField(default=timezone.now)
    #emailed_to = models.ManyToManyField(EmailedTo, blank=True)
    emailed_to = ArrayField(models.EmailField(blank=True), blank=True)
    date_last_used = models.DateField(default=timezone.now)
    deprecated = models.BooleanField(default=False)

    def __str__(self):
        return self.email_subject


#############
# NewsItems #
#############

class NewsItem(models.Model):
    date = models.DateField()
    headline = models.CharField(max_length=300)
    blurb = models.TextField()
    followup_link = models.URLField(blank=True, null=True)
    followup_link_text = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ', ' + self.headline

    def descriptor_full(self):
        """ For News page. """
        descriptor = ('<div class="flex-greybox640">'
                      '<h3 class="NewsHeadline">{{ headline }}</h3>'
                      '<p>{{ date }}</p>'
                      '<p>{{ blurb }}</p>'
                  )
        context = Context({'headline': self.headline, 
                           'date': self.date.strftime('%Y-%m-%d'),
                           'blurb': self.blurb,})
        if self.followup_link:
            descriptor += '<p><a href="{{ followup_link }}">{{ followup_link_text }}</a></p>'
            context['followup_link'] = self.followup_link
            context['followup_link_text'] = self.followup_link_text
        descriptor += '</div>'
        template = Template(descriptor)
        return template.render(context)


    def descriptor_small(self):
        """ For index page. """
        descriptor = ('<h3 class="NewsHeadline">{{ headline }}</h3>'
                      '<p>{{ date }}</p>'
                      '<p>{{ blurb }}</p>'
                  )
        context = Context({'headline': self.headline, 
                           'date': self.date.strftime('%Y-%m-%d'),
                           'blurb': self.blurb,})
        if self.followup_link:
            descriptor += '<p><a href="{{ followup_link }}">{{ followup_link_text }}</a></p>'
            context['followup_link'] = self.followup_link
            context['followup_link_text'] = self.followup_link_text
        template = Template(descriptor)
        return template.render(context)


        
#########
# Lists #
#########

class List(models.Model):
    """
    A collection of commentaries, submissions, thesislinks, comments, etc
    defined by a Contributor, for use in Graphs, etc
    """
    owner = models.ForeignKey(Contributor)
    private = models.BooleanField(default=True)
    teams_with_access = models.ManyToManyField('scipost.Team', blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    submissions = models.ManyToManyField('submissions.Submission', blank=True, 
                                         related_name='list_submissions')
    commentaries = models.ManyToManyField('commentaries.Commentary', blank=True, 
                                          related_name='list_commentaries')
    thesislinks = models.ManyToManyField('theses.ThesisLink', blank=True, 
                                         related_name='list_thesislinks')
    comments = models.ManyToManyField('comments.Comment', blank=True, 
                                      related_name='list_comments')

    class Meta:
        default_permissions = ['add', 'view', 'change', 'delete']


    def __str__(self):
        return (self.title[:30] + ' (owner: ' + self.owner.user.first_name + ' ' 
                + self.owner.user.last_name + ')')


    def header(self):
        context = Context({'id': self.id, 'title': self.title,
                           'first_name': self.owner.user.first_name,
                           'last_name': self.owner.user.last_name})
        template = Template('''
        <p>List <a href="{% url 'scipost:list' list_id=id %}">{{ title }}
        </a> (owner: {{ first_name }} {{ last_name }})</p>
        ''')
        return template.render(context)


    def header_as_li(self):
        context = Context({'id': self.id, 'title': self.title,
                           'first_name': self.owner.user.first_name,
                           'last_name': self.owner.user.last_name})
        template = Template('''
        <li><p>List <a href="{% url 'scipost:list' list_id=id %}">
        {{ title }}</a> (owner: {{ first_name }} {{ last_name }})</p></li>
        ''')
        return template.render(context)


    def contents(self):
        context = Context({})
        output = '<p>' + self.description + '</p>'
        output += '<hr class="hr6"/>'
        emptylist = True
        if self.submissions.exists():
            emptylist = False
            output += '<p>Submissions:<ul>'
            for submission in self.submissions.all():
                output += submission.simple_header_as_li()
            output += '</ul></p>'
        if self.commentaries.exists():
            emptylist = False
            output += '<p>Commentaries:<ul>'
            for commentary in self.commentaries.all():
                output += commentary.simple_header_as_li()
            output += '</ul></p>'
        if self.thesislinks.exists():
            emptylist = False
            output += '<p>Thesislinks:<ul>'
            for thesislink in self.thesislinks.all():
                output += thesislink.simple_header_as_li()
            output += '</ul></p>'
        if self.comments.exists():
            emptylist = False
            output += '<p>Comments:<ul>'
            for comment in self.comments.all():
                output += comment.simple_header_as_li()
            output += '</ul></p>'
        if emptylist:
            output += '<br/><h3>This List is empty.</h3>'
        template = Template(output)
        return template.render(context)


#########
# Teams #
#########

class Team(models.Model):
    """
    Team of Contributors, to enable private collaborations.
    """
    leader = models.ForeignKey(Contributor)
    members = models.ManyToManyField (Contributor, blank=True, related_name='team_members')
    name = models.CharField(max_length=100)
    established = models.DateField(default=timezone.now)

    class Meta:
        default_permissions = ['add', 'view', 'change', 'delete']


    def __str__(self):
        return (self.name + ' (led by ' + self.leader.user.first_name + ' ' 
                + self.leader.user.last_name + ')')

    def header_as_li(self):
        context = Context({'name': self.name,})
        output = ('<li><p>Team {{ name }}, led by ' + self.leader.user.first_name + ' ' 
                  + self.leader.user.last_name + '</p>')
        output += '<p>Members: '
        if not self.members.all():
            output += '(none yet, except for the leader)'
        else :
            for member in self.members.all():
                output += member.user.first_name + ' ' + member.user.last_name + ', '
        output += '</p></li>'
        template = Template(output)
        return template.render(context)


##########
# Graphs #
##########

class Graph(models.Model):
    """ 
    A Graph is a collection of Nodes with directed arrows,
    representing e.g. a reading list, exploration path, etc.
    If private, only the teams in teams_with_access can see/edit it.
    """
    owner = models.ForeignKey(Contributor)
    private = models.BooleanField(default=True)
    teams_with_access = models.ManyToManyField(Team, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        default_permissions = ['add', 'view', 'change', 'delete']


    def __str__(self):
        return (self.title[:30] + ' (owner: ' + self.owner.user.first_name + ' ' 
                + self.owner.user.last_name + ')')

    def header_as_li(self):
        context = Context({'id': self.id, 'title': self.title, 
                           'first_name': self.owner.user.first_name, 
                           'last_name': self.owner.user.last_name})
        template = Template('''
        <li><p>Graph <a href="{% url 'scipost:graph' graph_id=id %}">
        {{ title }}</a> (owner: {{ first_name }} {{ last_name }})</li>
        ''')
        return template.render(context)

    def contents(self):
        context = Context({})
        output = self.description
        template = Template(output)
        return template.render(context)


class Node(models.Model):
    """
    Node of a graph (directed).
    Each node is composed of a set of submissions, commentaries, thesislinks. 
    Accessibility rights are set in the Graph ForeignKey.
    """
    graph = models.ForeignKey(Graph, default=None)
    added_by = models.ForeignKey(Contributor, default=None)
    created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    submissions = models.ManyToManyField('submissions.Submission', blank=True, 
                                         related_name='node_submissions')
    commentaries = models.ManyToManyField('commentaries.Commentary', blank=True, 
                                          related_name='node_commentaries')
    thesislinks = models.ManyToManyField('theses.ThesisLink', blank=True, 
                                         related_name='node_thesislinks')

    class Meta:
        default_permissions = ['add', 'view', 'change', 'delete']


    def __str__(self):
        return self.graph.title[:20] + ': ' + self.name[:20] 

    def header_as_p(self):
        context = Context({'graph_id': self.graph.id, 'id': self.id, 'name': self.name})
        output = ('<p class="node_p" id="node_id{{ id }}">'
                  '<a href="{% url \'scipost:graph\' graph_id=graph_id %}">{{ name }}</a></p>')
        template = Template(output)
        return template.render(context)

    def contents(self):
        context = Context({'graph_id': self.graph.id, 
                           'id': self.id, 'name': self.name, 
                           'description': self.description})
        output = ('<div class="node_contents node_id{{ id }}">'
                  + '<h3>{{ name }}</h3><p>{{ description }}</p></div>')
        template = Template(output)
        return template.render(context)

    def contents_small(self):
        output = '<div style="font-size: 60%">' + self.contents + '</div>'
        template = Template(output)
        return template.render()


ARC_LENGTHS = [
#    (4, '4'), (8, '8'), (16, '16'), (32, '32'), (64, '64'), (128, '128')
    (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'),
    ]

class Arc(models.Model):
    """
    Arc of a graph, linking two nodes.
    The length is user-adjustable.
    """
    graph = models.ForeignKey(Graph, default=None)
    added_by = models.ForeignKey(Contributor, default=None)
    created = models.DateTimeField(default=timezone.now)
    source = models.ForeignKey(Node, related_name='source')
    target = models.ForeignKey(Node, related_name='target')
    length = models.PositiveSmallIntegerField(choices=ARC_LENGTHS, default=32)

