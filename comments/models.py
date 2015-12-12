from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *
#from commentaries.models import *
#from contributors.models import *
##from journals.models import *
##from ratings.models import *
#from reports.models import *
#from submissions.models import *

from commentaries.models import Commentary
from contributors.models import Contributor
from reports.models import Report
from submissions.models import Submission

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

    def __str__ (self):
        return self.comment_text


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

    def __str__ (self):
        return self.reply_text

