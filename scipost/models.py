from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

# All definitions for models (some also for forms):

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
    (2, 'SciPost Commentary Editor'),
    (3, 'SciPost Journal Editor'),
    (4, 'SciPost Journal Editor-in-chief'),
    (5, 'SciPost Lead Editor'),
    (-1, 'not a professional scientist'),
    (-2, 'other account already exists'),
    (-3, 'barred from SciPost'),
    (-4, 'account disabled'),
    )

COMMENTARY_TYPES = (
    ('published', 'published paper'),
    ('preprint', 'arXiv preprint (from at least 4 weeks ago)'),
    )

SCIPOST_JOURNALS = (
    ('SciPost Physics Select', 'SciPost Physics Select'),
    ('SciPost Physics Letters', 'SciPost Physics Letters'),
    ('SciPost Physics X', 'SciPost Physics X (cross-division)'),
#    ('SciPost Physics Rapid', 'SciPost Physics Rapid'),
# Possible further specializations: instead of SciPost Physics,
#    ('SciPost Physics A', 'SciPost Physics A (Atomic, Molecular and Optical Physics)'),
#    ('SciPost Physics C', 'SciPost Physics C (Condensed Matter Physics)'),
#    ('SciPost Physics H', 'SciPost Physics H (High-energy Physics)'),
#    ('SciPost Physics M', 'SciPost Physics M (Mathematical Physics)'),
#    ('SciPost Physics N', 'SciPost Physics N (Numerical and Computational Physics)'),
#    ('SciPost Physics Q', 'SciPost Physics Q (Quantum Statistical Mechanics)'),
#    ('SciPost Physics S', 'SciPost Physics S (Classical Statistical and Soft Matter Physics)'), 
# Use the three fundamental branches of Physics: 
#    ('SciPost Physics E', 'SciPost Physics E (Experimental)'),
#    ('SciPost Physics T', 'SciPost Physics T (Theoretical)'),
#    ('SciPost Physics C', 'SciPost Physics C (Computational)'),
# Unified:
    ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'),
    )

SCIPOST_JOURNALS_SUBMIT = ( # Same as SCIPOST_JOURNALS, but SP Select deactivated
#    ('SciPost Physics Select', 'SciPost Physics Select'), # cannot be submitted to: promoted from Letters
    ('SciPost Physics Letters', 'SciPost Physics Letters'),
    ('SciPost Physics X', 'SciPost Physics X (cross-division)'),
# Use the three fundamental branches of Physics: 
#    ('SciPost Physics E', 'SciPost Physics E (Experimental)'),
#    ('SciPost Physics T', 'SciPost Physics T (Theoretical)'),
#    ('SciPost Physics C', 'SciPost Physics C (Computational)'),
# Unified:
    ('SciPost Physics', 'SciPost Physics (Experimental, Theoretical and Computational)'),
    )

SCIPOST_JOURNALS_DOMAINS = (
    ('E', 'Experimental'),
    ('T', 'Theoretical'),
    ('C', 'Computational'),
)

SCIPOST_JOURNALS_SPECIALIZATIONS = (
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

SUBMISSION_STATUS = (
    (0, 'unassigned'),
    (1, 'editor in charge assigned'),
    (2, 'under review'),
    (3, 'reviewed, peer checking period'),
    (4, 'reviewed, peer checked, editorial decision pending'),
    (5, 'editorial decision'),
    )

TITLE_CHOICES = (
    ('PR', 'Prof.'),
    ('DR', 'Dr'),
    ('MR', 'Mr'),
    ('MRS', 'Mrs'),
    )

RATING_CHOICES = (
    (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')
    )

REPORT_REC = (
    (1, 'Publish as Tier I (top 10% of papers in this journal)'),
    (2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (3, 'Publish as Tier III (meets the criteria of this journal)'),
    (-1, 'Ask for minor revision'),
    (-2, 'Ask for major revision'),
    (-3, 'Reject')
    )

class Contributor(models.Model):
    """ All users of SciPost are Contributors. Permissions determine the sub-types. """
    user = models.OneToOneField(User)
    rank = models.SmallIntegerField(default=0, choices=CONTRIBUTOR_RANKS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    # username, password, email, first_name and last_name are inherited from User
    orcid_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="ORCID id", default='')
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, blank=True, verbose_name="address")
    personalwebpage = models.URLField(blank=True, verbose_name='personal web page')
    nr_reports = models.PositiveSmallIntegerField(default=0)
    report_clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    report_correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    report_usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    nr_comments = models.PositiveSmallIntegerField(default=0)
    comment_clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    comment_correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    comment_usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    def __str__ (self):
        return self.user.username


class Commentary(models.Model):
    """ A Commentary contains all the contents of a SciPost Commentary page for a given publication. """
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey (Contributor, blank=True, null=True)
    type = models.CharField(max_length=9) # published paper or arxiv preprint
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    pub_DOI_link = models.URLField(verbose_name='DOI link to the original publication')
    author_list = models.CharField(max_length=1000)
    pub_date = models.DateField(verbose_name='date of original publication')
    pub_abstract = models.TextField()
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.pub_title

class CommentaryRating(models.Model):
    """ A Commentary rating is a set of numbers quantifying the original publication subject to a Commentary. """
    commentary = models.ForeignKey(Commentary)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)



class Submission(models.Model):
    submitted_by = models.ForeignKey(Contributor)
    vetted = models.BooleanField(default=False)
    editor_in_charge = models.ForeignKey(Contributor, related_name="editor_in_charge", blank=True, null=True) # assigned by Journal Editor    open_for_reporting = models.BooleanField(default=False)
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS)
    domain = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_DOMAINS, default='E')
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.SmallIntegerField(choices=SUBMISSION_STATUS) # set by Editors
    open_for_reporting = models.BooleanField(default=True)
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000)
    abstract = models.TextField()
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    submission_date = models.DateField(verbose_name='date of original publication')
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.title

class SubmissionRating(models.Model):
    """ A Submission rating is a set of numbers quantifying various requirements of a Submission. """
    submission = models.ForeignKey(Submission)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)




class Report(models.Model):    
    """ Both types of reports, invited or contributed. """
    # status:
    # 1: vetted (by Contributor with rank >= 2) 
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    status = models.SmallIntegerField(default=0)
    submission = models.ForeignKey(Submission)
    author = models.ForeignKey(Contributor)
    qualification = models.PositiveSmallIntegerField(default=0)
    strengths = models.TextField()
    weaknesses = models.TextField()
    report = models.TextField()
    requested_changes = models.TextField()
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    date_invited = models.DateTimeField('date invited', blank=True, null=True)
    invited_by = models.ForeignKey(Contributor, blank=True, null=True, related_name='invited_by')
    date_submitted = models.DateTimeField('date submitted')
    # Aggregates of ratings applied to this report:
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

class ReportRating(models.Model):
    """ A Report rating is a set of numbers quantifying various requirements of a Report. """
    report = models.ForeignKey(Report)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class Comment(models.Model):
    """ A Comment is an unsollicited note, submitted by a Contributor, on a particular publication or in reply to an earlier Comment. """
    # status:
    # 1: vetted (by Contributor with rank >= 2) 
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    status = models.SmallIntegerField(default=0)
    commentary = models.ForeignKey(Commentary, blank=True, null=True) # a Comment is either for a Commentary or Submission
    submission = models.ForeignKey(Submission, blank=True, null=True)
    in_reply_to = models.ForeignKey('self', blank=True, null=True)
    author = models.ForeignKey(Contributor)
    comment_text = models.TextField()
    date_submitted = models.DateTimeField('date submitted')
    # Aggregates of ratings applied to this comment:
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    def __str__ (self):
        return self.comment_text

class CommentRating(models.Model):
    """ A Comment rating is a set of numbers quantifying various requirements of a Comment. """
    comment = models.ForeignKey(Comment)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class AuthorReply(models.Model):
    """ Reply to a Comment or Report. """
    # status:
    # 1: vetted (by Contributor with rank >= 2) 
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    status = models.SmallIntegerField(default=0)
    commentary = models.ForeignKey(Commentary, blank=True, null=True)
    submission = models.ForeignKey(Submission, blank=True, null=True)
    in_reply_to_comment = models.ForeignKey(Comment, blank=True, null=True) # one of this and next must be not null
    in_reply_to_report = models.ForeignKey(Report, blank=True, null=True)
    author = models.ForeignKey(Contributor)
    reply_text = models.TextField()
    date_submitted = models.DateTimeField('date submitted')
    # Aggregates of ratings applied to this comment:
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)

    def __str__ (self):
        return self.reply_text

class AuthorReplyRating(models.Model):
    reply = models.ForeignKey(AuthorReply)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)

