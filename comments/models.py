from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.utils.safestring import mark_safe

from .models import *

from commentaries.models import Commentary
from scipost.models import Contributor
from submissions.models import Submission, Report
from theses.models import ThesisLink

COMMENT_CATEGORIES = (
    ('ERR', 'erratum'),
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
    """ A Comment is an unsollicited note, submitted by a Contributor,
    on a particular publication or in reply to an earlier Comment. """

    status = models.SmallIntegerField(default=0)
    vetted_by = models.ForeignKey(Contributor, blank=True, null=True,
                                  on_delete=models.CASCADE,
                                  related_name='comment_vetted_by')
    # a Comment is either for a Commentary or Submission
    commentary = models.ForeignKey(Commentary, blank=True, null=True, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, blank=True, null=True, on_delete=models.CASCADE)
    thesislink = models.ForeignKey(ThesisLink, blank=True, null=True, on_delete=models.CASCADE)
    is_author_reply = models.BooleanField(default=False)
    in_reply_to_comment = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    in_reply_to_report = models.ForeignKey(Report, blank=True, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(Contributor, default=1, on_delete=models.CASCADE)
    anonymous = models.BooleanField(default=False, verbose_name='Publish anonymously')
    # Categories:
    is_cor = models.BooleanField(default=False, verbose_name='correction/erratum')
    is_rem = models.BooleanField(default=False, verbose_name='remark')
    is_que = models.BooleanField(default=False, verbose_name='question')
    is_ans = models.BooleanField(default=False, verbose_name='answer to question')
    is_obj = models.BooleanField(default=False, verbose_name='objection')
    is_rep = models.BooleanField(default=False, verbose_name='reply to objection')
    is_val = models.BooleanField(default=False, verbose_name='validation or rederivation')
    is_lit = models.BooleanField(default=False, verbose_name='pointer to related literature')
    is_sug = models.BooleanField(default=False, verbose_name='suggestion for further work')
    comment_text = models.TextField()
    remarks_for_editors = models.TextField(default='', blank=True,
                                           verbose_name='optional remarks for the Editors only')
    date_submitted = models.DateTimeField('date submitted')
    # Opinions
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField(Contributor,
                                          related_name='in_agreement', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField(Contributor,
                                        related_name='in_notsure', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField(Contributor,
                                             related_name='in_disagreement', blank=True)

    def __str__ (self):
        return ('by ' + self.author.user.first_name + ' ' + self.author.user.last_name +
                ' on ' + self.date_submitted.strftime('%Y-%m-%d') + ', '   + self.comment_text[:30])


    def update_opinions(self, contributor_id, opinion):
        contributor = get_object_or_404(Contributor, pk=contributor_id)
        self.in_agreement.remove(contributor)
        self.in_notsure.remove(contributor)
        self.in_disagreement.remove(contributor)
        if opinion == 'A':
            self.in_agreement.add(contributor)
        elif opinion == 'N':
            self.in_notsure.add(contributor)
        elif opinion == 'D':
            self.in_disagreement.add(contributor)
        self.nr_A = self.in_agreement.count()
        self.nr_N = self.in_notsure.count()
        self.nr_D = self.in_disagreement.count()
        self.save()


    def opinions_as_ul(self):
        template = Template('''
        <ul class="opinionsDisplay">
        <li style="background-color: #000099">Agree {{ nr_A }}</li>
        <li style="background-color: #555555">Not sure {{ nr_N }}</li>
        <li style="background-color: #990000">Disagree {{ nr_D }}</li>
        </ul>
        ''')
        context = Context ({'nr_A': self.nr_A, 'nr_N': self.nr_N, 'nr_D': self.nr_D})
        return template.render(context)


    def opinions_as_ul_tiny(self):
        template = Template('''
        <ul class="opinionsDisplay">
        <li style="background-color: #000099; font-size: 8px; padding: 2px;">Agree {{ nr_A }}</li>
        <li style="background-color: #555555; font-size: 8px; padding: 2px;">Not sure {{ nr_N }}</li>
        <li style="background-color: #990000; font-size: 8px; padding: 2px;">Disagree {{ nr_D }}</li>
        </ul>
        ''')
        context = Context ({'nr_A': self.nr_A, 'nr_N': self.nr_N, 'nr_D': self.nr_D})
        return template.render(context)


    def print_identifier (self):
        # for display
        output = '<div class="commentid">\n'
        output += '<h3><a id="comment_id{{ id }}"></a>'
        context = Context({'id': self.id})
        if self.is_author_reply:
            output += 'Author '
        if not self.anonymous:
            output += (' <a href="/contributor/{{ author_id }}">'
                       + '{{ first_name }} {{ last_name }}</a> on ')
            context['author_id'] = self.author.id
            context['first_name'] = self.author.user.first_name
            context['last_name'] = self.author.user.last_name
        output += '{{ date_comment_submitted }}'
        context['date_comment_submitted'] = self.date_submitted.strftime("%Y-%m-%d")
        if self.in_reply_to_comment:
            output += (' (in reply to <a href="#comment_id{{ in_reply_to_comment_id }}">'
                       '{{ in_reply_to_comment_first_name }} '
                       '{{ in_reply_to_comment_last_name }} on '
                       '{{ in_reply_to_comment_date }}</a>)')
            context['in_reply_to_comment_id'] = self.in_reply_to_comment_id
            context['in_reply_to_comment_first_name'] = (self.in_reply_to_comment
                                                         .author.user.first_name)
            context['in_reply_to_comment_last_name'] = (self.in_reply_to_comment
                                                        .author.user.last_name)
            context['in_reply_to_comment_date'] = (self.in_reply_to_comment
                                                   .date_submitted.strftime("%Y-%m-%d"))
        elif self.in_reply_to_report:
            output += ' (in reply to <a href="#report_id{{ in_reply_to_report_id }}">'
            context['in_reply_to_report_id'] = self.in_reply_to_report_id
            if not self.in_reply_to_report.anonymous:
                output += '{{ in_reply_to_report_first_name }} {{ in_reply_to_report_last_name}}'
                context['in_reply_to_report_first_name'] = (self.in_reply_to_report
                                                            .author.user.first_name)
                context['in_reply_to_report_last_name'] = (self.in_reply_to_report
                                                           .author.user.last_name)
            else:
                output += 'Report {{ in_reply_to_report_id }}'
                context['in_reply_to_report_id'] = self.in_reply_to_report_id
            output += ' on {{ date_report_submitted }}</a>)'
            context['date_report_submitted'] = self.in_reply_to_report.date_submitted.strftime("%Y-%m-%d")
        output += '</h3></div>'
        template = Template(output)
        return template.render(context)


    def print_identifier_for_vetting (self):
        # for display, same as print_identifier but named even if anonymous, not linked
        output = '<div class="commentid">\n'
        output += '<h3>'
        context = Context()
        if self.is_author_reply:
            output += 'Author '
        output += ' <a href="/contributor/{{ author_id }}">{{ first_name }} {{ last_name }}</a> on '
        context['author_id'] = self.author.id
        context['first_name'] = self.author.user.first_name
        context['last_name'] = self.author.user.last_name
        output += '{{ date_submitted }}'
        context['date_submitted'] = self.date_submitted.strftime("%Y-%m-%d")
        if self.in_reply_to_comment:
            output += (' (in reply to <a href="#comment_id{{ in_reply_to_comment_id }}">'
                       '{{ in_reply_to_comment_first_name }} {{ in_reply_to_comment_last_name }} '
                       'on {{ in_reply_to_comment_date }}</a>)')
            context['in_reply_to_comment_id'] = self.in_reply_to_comment_id
            context['in_reply_to_comment_first_name'] = (self.in_reply_to_comment
                                                         .author.user.first_name)
            context['in_reply_to_comment_last_name'] = (self.in_reply_to_comment
                                                        .author.user.last_name)
            context['in_reply_to_comment_date'] = (self.in_reply_to_comment
                                                   .date_submitted.strftime("%Y-%m-%d"))
        elif self.in_reply_to_report:
            output += ' (in reply to <a href="#report_id{{ in_reply_to_report_id }}">'
            context['in_reply_to_report_id'] = self.in_reply_to_report_id
            if not self.in_reply_to_report.anonymous:
                output += '{{ in_reply_to_report_first_name }} {{ in_reply_to_report_last_name}}'
                context['in_reply_to_report_first_name'] = (self.in_reply_to_report
                                                            .author.user.first_name)
                context['in_reply_to_report_last_name'] = (self.in_reply_to_report
                                                           .author.user.last_name)
            else:
                output += 'Report {{ in_reply_to_report_id }}'
                context['in_reply_to_report_id'] = self.in_reply_to_report_id
            output += '</a> on {{ date_submitted }})'
            context['date_submitted'] = self.in_reply_to_report.date_submitted.strftime("%Y-%m-%d")
        output += '</h3></div>'
        template = Template(output)
        return template.render(context)


    def header_as_li (self):
        # for search lists
        header = '<li>'
        #header += '<div class="flex-container"><div class="flex-whitebox0">'
        header += 'Nr {{ id }}'
        context = Context({'id': self.id})
        header += ', <div class="opinionsDisplay">' + self.opinions_as_ul_tiny() + '</div>'
        if self.status <= 0:
            header += (', status: <span style="color:red">'
                       + comment_status_dict[self.status] + '</span>')
        text_cut = self.comment_text[:50]
        if len(self.comment_text) > 50:
            text_cut += '...'
        context['id'] = self.id
        context['text_cut'] = text_cut
        context['date_submitted'] = self.date_submitted.strftime("%Y-%m-%d")
        header += ': '
        if not self.anonymous:
            header += (' <a href="/contributor/{{ author_id }}">'
                       '{{ first_name }} {{ last_name }}</a>, ')
            context['author_id'] = self.author.id
            context['first_name'] = self.author.user.first_name
            context['last_name'] = self.author.user.last_name
        if self.submission is not None:
            header += ('<a href="/submission/{{ arxiv_identifier_w_vn_nr }}#comment_id{{ id }}">'
                       ' \"{{ text_cut }}\"</a><p>submitted on {{ date_submitted }}')
            header += (' in submission on <a href="/submission/{{ arxiv_identifier_w_vn_nr }}"'
                       ' class="pubtitleli">{{ submission_title }}</a> by '
                       '{{ submission_author_list }}</p>')
            context['arxiv_identifier_w_vn_nr'] = self.submission.arxiv_identifier_w_vn_nr
            context['submission_title'] = self.submission.title
            context['submission_author_list'] = self.submission.author_list
        if self.commentary is not None:
            header += ('<a href="/commentary/{{ commentary_url }}#comment_id{{ id }}">'
                       ' \"{{ text_cut }}\"</a><p>submitted on {{ date_submitted }}')
            header += (' in commentary on <a href="/commentary/{{ commentary_url }}"'
                       ' class="pubtitleli">'
                       '{{ commentary_pub_title }}</a> by {{ commentary_author_list }}</p>')
            context['commentary_url'] = self.commentary.arxiv_or_DOI_string
            context['commentary_pub_title'] = self.commentary.pub_title
            context['commentary_author_list'] = self.commentary.author_list
        if self.thesislink is not None:
            header += ('<a href="/thesis/{{ thesislink_id }}#comment_id{{ id }}">'
                       ' \"{{ text_cut }}\"</a><p>submitted on {{ date_submitted }}')
            header += (' in thesislink on <a href="/thesis/{{ thesislink_id }}" class="pubtitleli">'
                       '{{ thesislink_title }}</a> by {{ thesislink_author }}</p>')
            context['thesislink_id'] = self.thesislink.id
            context['thesislink_title'] = self.thesislink.title
            context['thesislink_author'] = self.thesislink.author
        #header += '</div></div>'
        header += '</li>'
        template = Template(header)
        return template.render(context)


    def simple_header_as_li (self):
        # for Lists
        header = '<li>'
        #header += '<div class="flex-container"><div class="flex-whitebox0">'
        context = Context({})
        text_cut = self.comment_text[:30]
        if len(self.comment_text) > 30:
            text_cut += '...'
        context['text_cut'] = text_cut
        if not self.anonymous:
            header += ' <a href="/contributor/{{ author_id }}">{{ first_name }} {{ last_name }}</a>, '
            context['author_id'] = self.author.id
            context['first_name'] = self.author.user.first_name
            context['last_name'] = self.author.user.last_name
        if self.submission is not None:
            header += ('<a href="/submission/{{ arxiv_identifier_w_vn_nr }}#comment_id{{ id }}"> '
                       '\"{{ text_cut }}\"</a>'
                       ' in submission on <a href="/submission/{{ arxiv_identifier_w_vn_nr }}" class="pubtitleli">'
                       '{{ submission_title }}</a> by {{ submission_author_list }}</p>')
            context['arxiv_identifier_w_vn_nr'] = self.submission.arxiv_identifier_w_vn_nr
            context['submission_title'] = self.submission.title
            context['submission_author_list'] = self.submission.author_list
        if self.commentary is not None:
            header += ('<a href="/commentary/{{ commentary_url }}#comment_id{{ id }}"> '
                       '\"{{ text_cut }}\"</a>'
                       ' in commentary on <a href="/commentary/{{ commentary_url }}" class="pubtitleli">'
                       '{{ commentary_pub_title }}</a> by {{ commentary_author_list }}</p>')
            context['commentary_url'] = self.commentary.arxiv_or_DOI_string
            context['commentary_pub_title'] = self.commentary.pub_title
            context['commentary_author_list'] = self.commentary.author_list
        if self.thesislink is not None:
            header += '<a href="/thesis/{{ thesislink_id }}#comment_id{{ id }}"> \"{{ text_cut }}\"</a>'
            header += (' in thesislink on <a href="/thesis/{{ thesislink_id }}" class="pubtitleli">' +
                       '{{ thesislink_title }}</a> by {{ thesislink_author }}</p>')
            context['thesislink_id'] = self.thesislink.id
            context['thesislink_title'] = self.thesislink.title
            context['thesislink_author'] = self.thesislink.author
        #header += '</div></div>'
        header += '</li>'
        template = Template(header)
        return template.render(context)


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
        if self.is_cor:
            output += '<li>correction</li>'
        if self.is_val:
            output += '<li>validation or rederivation</li>'
        if self.is_lit:
            output += '<li>pointer to related literature</li>'
        if self.is_sug:
            output += '<li>suggestion for further work</li>'
        output += '</ul></div>'
        return mark_safe(output)
