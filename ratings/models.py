
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from commentaries.models import Commentary
from comments.models import Comment, AuthorReply
from contributors.models import Contributor
from reports.models import Report
from submissions.models import Submission


RATING_CHOICES = (
    (101, 'abstain'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
    (100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')
    )


class Rating(models.Model):
    """ Abstract base class for all ratings. """
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(RATING_CHOICES, default=0, null=True)
    validity = models.PositiveSmallIntegerField(RATING_CHOICES, default=0, null=True)
    rigour = models.PositiveSmallIntegerField(RATING_CHOICES, default=0, null=True)
    originality = models.PositiveSmallIntegerField(RATING_CHOICES, default=0, null=True)
    significance = models.PositiveSmallIntegerField(RATING_CHOICES, default=0, null=True)
    
    class Meta:
        abstract = True


class CommentaryRating(Rating):
    """ A Commentary rating is a set of numbers quantifying the original publication subject to a Commentary. """
    commentary = models.ForeignKey(Commentary)


class CommentRating(Rating):
    """ A Comment rating is a set of numbers quantifying various requirements of a Comment. """
    comment = models.ForeignKey(Comment)

class AuthorReplyRating(Rating):
    reply = models.ForeignKey(AuthorReply)


class ReportRating(Rating):
    """ A Report rating is a set of numbers quantifying various requirements of a Report. """
    report = models.ForeignKey(Report)


class SubmissionRating(Rating):
    """ A Submission rating is a set of numbers quantifying various requirements of a Submission. """
    submission = models.ForeignKey(Submission)



