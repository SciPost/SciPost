
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

#from commentaries.models import *
#from comments.models import *
#from contributors.models import *
#from journals.models import *
#from reports.models import *
#from scipost.models import *
#from submissions.models import *

from commentaries.models import Commentary
from comments.models import Comment, AuthorReply
from contributors.models import Contributor
from reports.models import Report
from submissions.models import Submission


RATING_CHOICES = (
    (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')
    )


class CommentaryRating(models.Model):
    """ A Commentary rating is a set of numbers quantifying the original publication subject to a Commentary. """
    commentary = models.ForeignKey(Commentary)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class SubmissionRating(models.Model):
    """ A Submission rating is a set of numbers quantifying various requirements of a Submission. """
    submission = models.ForeignKey(Submission)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class ReportRating(models.Model):
    """ A Report rating is a set of numbers quantifying various requirements of a Report. """
    report = models.ForeignKey(Report)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class CommentRating(models.Model):
    """ A Comment rating is a set of numbers quantifying various requirements of a Comment. """
    comment = models.ForeignKey(Comment)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)


class AuthorReplyRating(models.Model):
    reply = models.ForeignKey(AuthorReply)
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES)
    correctness = models.PositiveSmallIntegerField(RATING_CHOICES)
    usefulness = models.PositiveSmallIntegerField(RATING_CHOICES)

