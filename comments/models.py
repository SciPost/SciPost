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
from scipost.models import Contributor
from submissions.models import Submission, Report
from theses.models import ThesisLink

COMMENT_CATEGORIES = (
    ('REM', 'remark'),
    ('QUE', 'question'),
    ('ANS', 'answer to question'),
    ('OBJ', 'objection'),
    ('REP', 'reply to objection'),
    ('VAL', 'validation or rederivation'),
    ('LIT', 'pointer to related literature'),
    ('SUG', 'suggestion for further work'),
    )

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
    thesislink = models.ForeignKey(ThesisLink, blank=True, null=True)
    in_reply_to = models.ForeignKey('self', blank=True, null=True)
    author = models.ForeignKey(Contributor)
    anonymous = models.BooleanField(default=False, verbose_name='Publish anonymously')
    # Categories:
    is_rem = models.BooleanField(default=False, verbose_name='remark')
    is_que = models.BooleanField(default=False, verbose_name='question')
    is_ans = models.BooleanField(default=False, verbose_name='answer to question')
    is_obj = models.BooleanField(default=False, verbose_name='objection')
    is_rep = models.BooleanField(default=False, verbose_name='reply to objection')
    is_val = models.BooleanField(default=False, verbose_name='validation or rederivation')
    is_lit = models.BooleanField(default=False, verbose_name='pointer to related literature')
    is_sug = models.BooleanField(default=False, verbose_name='suggestion for further work')
    comment_text = models.TextField()
    remarks_for_editors = models.TextField(default='', blank=True, verbose_name='optional remarks for the Editors only')
    date_submitted = models.DateTimeField('date submitted')


    def __str__ (self):
        return self.comment_text

    def print_identifier (self):
        output = '<div class="commentid">\n'
        output += '<h3>' + str(self.id)
        if not self.anonymous:
            output += ' by ' + self.author.user.first_name + ' ' + self.author.user.last_name
        if self.in_reply_to:
            output += ' in reply to ' + str(self.in_reply_to.id) + '</h3>\n'
        output += '<h4>Date: ' + self.date_submitted.strftime("%Y-%m-%d") + '</h4>\n</div>\n'
        return output


class AuthorReply(models.Model):
    """ Reply to a Comment or Report. """
    # status:
    # 1: vetted (by Contributor with rank >= 2) 
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    # -4: not from author
    status = models.SmallIntegerField(default=0)
    commentary = models.ForeignKey(Commentary, blank=True, null=True)
    submission = models.ForeignKey(Submission, blank=True, null=True)
    thesislink = models.ForeignKey(ThesisLink, blank=True, null=True)
    in_reply_to_comment = models.ForeignKey(Comment, blank=True, null=True) # one of this and next must be not null
    in_reply_to_report = models.ForeignKey(Report, blank=True, null=True)
    author = models.ForeignKey(Contributor)
    reply_text = models.TextField(verbose_name="")
    date_submitted = models.DateTimeField('date submitted')

    def __str__ (self):
        return self.reply_text

