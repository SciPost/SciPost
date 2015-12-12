from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

#from commentaries.models import *
#from comments.models import *
#from contributors.models import *
#from journals.models import *
#from ratings.models import *
#from submissions.models import *

#from commentaries.models import Commentary
from contributors.models import Contributor
#from reports.models import Report
from submissions.models import Submission


REPORT_REC = (
    (1, 'Publish as Tier I (top 10% of papers in this journal)'),
    (2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (3, 'Publish as Tier III (meets the criteria of this journal)'),
    (-1, 'Ask for minor revision'),
    (-2, 'Ask for major revision'),
    (-3, 'Reject')
    )


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
    nr_relevance_ratings = models.IntegerField(default=0)
    relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_importance_ratings = models.IntegerField(default=0)
    importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_clarity_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_validity_ratings = models.IntegerField(default=0)
    validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_rigour_ratings = models.IntegerField(default=0)
    rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    

