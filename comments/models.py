from django.db import models
from django.shortcuts import get_object_or_404

from scipost.behaviors import TimeStampedModel
from scipost.models import Contributor

from .behaviors import validate_file_extension, validate_max_file_size
from .constants import COMMENT_STATUS, STATUS_PENDING
from .managers import CommentManager


class Comment(TimeStampedModel):
    """ A Comment is an unsollicited note, submitted by a Contributor,
    on a particular publication or in reply to an earlier Comment. """

    status = models.SmallIntegerField(default=STATUS_PENDING, choices=COMMENT_STATUS)
    vetted_by = models.ForeignKey('scipost.Contributor', blank=True, null=True,
                                  on_delete=models.CASCADE, related_name='comment_vetted_by')
    file_attachment = models.FileField(
        upload_to='uploads/comments/%Y/%m/%d/', blank=True,
        validators=[validate_file_extension, validate_max_file_size]
    )
    # a Comment is either for a Commentary or Submission or a ThesisLink.
    commentary = models.ForeignKey('commentaries.Commentary', blank=True, null=True,
                                   on_delete=models.CASCADE)
    submission = models.ForeignKey('submissions.Submission', blank=True, null=True,
                                   on_delete=models.CASCADE, related_name='comments')
    thesislink = models.ForeignKey('theses.ThesisLink', blank=True, null=True,
                                   on_delete=models.CASCADE)
    is_author_reply = models.BooleanField(default=False)
    in_reply_to_comment = models.ForeignKey('self', blank=True, null=True,
                                            related_name="nested_comments",
                                            on_delete=models.CASCADE)
    in_reply_to_report = models.ForeignKey('submissions.Report', blank=True, null=True,
                                           on_delete=models.CASCADE)
    author = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
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
    in_agreement = models.ManyToManyField(Contributor, related_name='in_agreement', blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField(Contributor, related_name='in_notsure', blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField(
        Contributor,
        related_name='in_disagreement',
        blank=True
    )

    objects = CommentManager()

    class Meta:
        permissions = (
            ('can_vet_comments', 'Can vet submitted Comments'),
        )

    def __str__(self):
        return ('by ' + self.author.user.first_name + ' ' + self.author.user.last_name +
                ' on ' + self.date_submitted.strftime('%Y-%m-%d') + ', ' + self.comment_text[:30])

    def get_author(self):
        '''Get author, if and only if comment is not anonymous!!!'''
        if not self.anonymous:
            return self.author
        return None

    def get_author_str(self):
        '''Get author string, if and only if comment is not anonymous!!!'''
        author = self.get_author()
        if author:
            return author.user.first_name + ' ' + author.user.last_name
        return 'Anonymous'

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
