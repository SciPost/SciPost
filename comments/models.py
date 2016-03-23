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
from scipost.models import Contributor, Opinion
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

COMMENT_STATUS = (
    (1, 'vetted'),
    (0, 'not yet vetted (pending)'),
    (-1, 'rejected (unclear)'),
    (-2, 'rejected (incorrect)'),
    (-3, 'rejected (not useful)'),
)
comment_status_dict = dict(COMMENT_STATUS)

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
    author = models.ForeignKey(Contributor, default=1)
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
    # Opinions 
    nr_A = models.PositiveIntegerField(default=0)
    nr_N = models.PositiveIntegerField(default=0)
    nr_D = models.PositiveIntegerField(default=0)

    def __str__ (self):
        return self.comment_text

    def recalculate_nr_opinions(self):
        self.nr_A = Opinion.objects.filter(comment=self, opinion='A').count()
        self.nr_N = Opinion.objects.filter(comment=self, opinion='N').count()
        self.nr_D = Opinion.objects.filter(comment=self, opinion='D').count()
        self.save()

    def opinions_as_ul(self):
        output = '<div class="opinionsDisplay"><ul>'
        output += '<li style="background-color: #000099">Agree: ' + str(self.nr_A) + '</li>'
        output += '<li style="background-color: #555555">Not sure: ' + str(self.nr_N) + '</li>'
        output += '<li style="background-color: #990000">Disagree: ' + str(self.nr_D) + '</li>'
        output += '</ul></div>'
        return output


    def print_identifier (self):
        output = '<div class="commentid">\n'
        #output += '<h3><a id="comment_id' + str(self.id) + '">' + str(self.id) + '</a>'
        output += '<h3><a id="comment_id' + str(self.id) + '"></a>'
        if not self.anonymous:
            output += (' <a href="/contributor/' + str(self.author.id) + '">' +
                       self.author.user.first_name + ' ' + self.author.user.last_name + '</a> on ')
        output += self.date_submitted.strftime("%Y-%m-%d")
        #output += '</h3>'
        if self.in_reply_to:
            #output += '<h4>in reply to ' + str(self.in_reply_to.id) + '</h4>\n'
            output += (' <a href="#comment_id' + str(self.in_reply_to_id) + '" style="font-size: 80%">(in reply to ' + str(self.in_reply_to.author.user.first_name) + ' ' + 
                       str(self.in_reply_to.author.user.last_name) + ' on ' + self.in_reply_to.date_submitted.strftime("%Y-%m-%d") + ')</a>')
        #output += '<h4>' + self.date_submitted.strftime("%Y-%m-%d") + '</h4>\n</div>\n'
        output += '</h3></div>'
        return output

    def header_as_li (self):
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0">'
        header += 'Nr ' + str(self.id)
        if self.status <= 0:
            header += ', status: <span style="color:red">' + comment_status_dict[self.status] + '</span>'
        text_cut = self.comment_text[:50]
        if len(self.comment_text) > 50:
            text_cut += '...'
        header += ': '
        if self.submission is not None:
            header += '<a href="/submission/' + str(self.submission.id) + '#comment_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in submission on <a href="/submission/' + str(self.submission.id) + '" class="pubtitleli">' + self.submission.title + '</a> by ' + self.submission.author_list + '</p></div>'
        if self.commentary is not None:
            header += '<a href="/commentary/' + str(self.commentary.id) + '#comment_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in commentary on <a href="/commentary/' + str(self.commentary.id) + '" class="pubtitleli">' + self.commentary.pub_title + '</a> by ' + self.commentary.author_list + '</p></div>'
        if self.thesislink is not None:
            header += '<a href="/thesis/' + str(self.thesislink.id) + '#comment_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in thesislink on <a href="/thesis/' + str(self.thesislink.id) + '" class="pubtitleli">' + self.thesislink.title + '</a> by ' + self.thesislink.author + '</p></div>'
        header += '</div></li>'
        return header

    def categories_as_ul(self):
        output = '<div class="commentcategorydisplay"><h4>Category:</h4><ul>'
        if self.is_rem:
            output += '<li>remark</li>'
        if self.is_que:
            output += '<li>question</li>'
        if self.is_ans:
            output += '<li>answer to question</li>'
        if self.is_obj:
            output += '<li>objection</li>'
        if self.is_rep:
            output += '<li>reply to objection</li>'
        if self.is_val:
            output += '<li>validation or rederivation</li>'
        if self.is_lit:
            output += '<li>pointer to related literature</li>'
        if self.is_sug:
            output += '<li>suggestion for further work</li>'
        output += '</ul></div>'
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
    author = models.ForeignKey(Contributor, default=1)
    reply_text = models.TextField(verbose_name="")
    date_submitted = models.DateTimeField('date submitted')

    def __str__ (self):
        return self.reply_text

    def print_identifier (self):
        output = '<div class="commentid">\n'
        output += '<h3><a id="authorreply_id' + str(self.id) + '">A' + str(self.id) + '</a>'
        output += ' by ' + self.author.user.first_name + ' ' + self.author.user.last_name + '</h3>'
        if self.in_reply_to_comment:
            output += '<p>in reply to <a id="comment_id' + str(self.in_reply_to_comment.id) + '">' + str(self.in_reply_to_comment.id) + '</a></p>\n'
        if self.in_reply_to_report:
            output += '<h4>in reply to ' + str(self.in_reply_to_report.id) + '</h4>\n'
        output += '<h4>Date: ' + self.date_submitted.strftime("%Y-%m-%d") + '</h4>\n</div>\n'
        return output

    def header_as_li (self):
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0">'
        header += 'Nr A' + str(self.id)
        if self.status <= 0:
            header += ', status: <span style="color:red">' + comment_status_dict[self.status] + '</span>'
        text_cut = self.reply_text[:50]
        if len(self.reply_text) > 50:
            text_cut += '...'
        header += ': '
        if self.submission is not None:
            header += '<a href="/submission/' + str(self.submission.id) + '#authorreply_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in submission on <a href="/submission/' + str(self.submission.id) + '" class="pubtitleli">' + self.submission.title + '</a> by ' + self.submission.author_list + '</p></div>'
        if self.commentary is not None:
            header += '<a href="/commentary/' + str(self.commentary.id) + '#authorreply_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in commentary on <a href="/commentary/' + str(self.commentary.id) + '" class="pubtitleli">' + self.commentary.pub_title + '</a> by ' + self.commentary.author_list + '</p></div>'
        if self.thesislink is not None:
            header += '<a href="/thesis/' + str(self.thesislink.id) + '#authorreply_id' + str(self.id) + '"> \"' + text_cut + '\"</a><p>submitted on ' + self.date_submitted.strftime("%Y-%m-%d")
            header += ' in thesislink on <a href="/thesis/' + str(self.thesislink.id) + '" class="pubtitleli">' + self.thesislink.pub_title + '</a> by ' + self.thesislink.author_list + '</p></div>'
        header += '</div></li>'
        return header

