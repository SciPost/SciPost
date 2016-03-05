
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from commentaries.models import Commentary
from comments.models import Comment, AuthorReply
from scipost.models import Contributor
from submissions.models import Submission, Report
from theses.models import ThesisLink

RATING_CHOICES = (
    (101, '-'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
    #(100, '100%'), (90, '90%'), (80, '80%'), (70, '70%'), (60, '60%'), (50, '50%'), (40, '40%'), (30, '30%'), (20, '20%'), (10, '10%'), (0, '0%')
    #(100, 'perfect'), (90, '--'), (80, 'excellent'), (70, '--'), (60, 'good'), (50, '--'), (40, 'reasonable'), (30, '--'), (20, 'acceptable'), (10, '--'), (0, 'below threshold')
    (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')
    )


class PublicationTypeRating(models.Model):
    """ Abstract base class for all ratings of publication-type objects. """
    rater = models.ForeignKey(Contributor)
    clarity = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    validity = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    rigour = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    originality = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    significance = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    
    class Meta:
        abstract = True


class CommentTypeRating(models.Model):
    """ Abstract base class for all ratings of comment-type objects. """
    rater = models.ForeignKey(Contributor)
    relevance = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    importance = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    clarity = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    validity = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    rigour = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=101)
    
    class Meta:
        abstract = True


class CommentaryRating(PublicationTypeRating):
    """ A Commentary rating is a set of numbers quantifying the original publication subject to a Commentary. """
    commentary = models.ForeignKey(Commentary)

class CommentRating(CommentTypeRating):
    """ A Comment rating is a set of numbers quantifying various requirements of a Comment. """
    comment = models.ForeignKey(Comment)

class AuthorReplyRating(CommentTypeRating):
    """ An AuthorReply rating is a set of numbers quantifying various requirements of an author's reply to a Comment. """
    authorreply = models.ForeignKey(AuthorReply)

class ReportRating(CommentTypeRating):
    """ A Report rating is a set of numbers quantifying various requirements of a Report. """
    report = models.ForeignKey(Report)

class SubmissionRating(PublicationTypeRating):
    """ A Submission rating is a set of numbers quantifying various requirements of a Submission. """
    submission = models.ForeignKey(Submission)

class ThesisLinkRating(PublicationTypeRating):
    """ A Thesis rating is a set of numbers quantifying various requirements of a Thesis. """
    thesislink = models.ForeignKey(ThesisLink)


