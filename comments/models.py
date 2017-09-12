from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django.urls import reverse

from guardian.shortcuts import assign_perm

from scipost.behaviors import TimeStampedModel
from scipost.models import Contributor

from .behaviors import validate_file_extension, validate_max_file_size
from .constants import COMMENT_STATUS, STATUS_PENDING
from .managers import CommentQuerySet


WARNING_TEXT = 'Warning: Rather use/edit `content_object` instead or be 100% sure you know what you are doing!'
US_NOTICE = 'Warning: This field is out of service and will be removed in the future.'


class Comment(TimeStampedModel):
    """ A Comment is an unsollicited note, submitted by a Contributor,
    on a particular publication or in reply to an earlier Comment. """

    status = models.SmallIntegerField(default=STATUS_PENDING, choices=COMMENT_STATUS)
    vetted_by = models.ForeignKey('scipost.Contributor', blank=True, null=True,
                                  on_delete=models.CASCADE, related_name='comment_vetted_by')
    file_attachment = models.FileField(upload_to='uploads/comments/%Y/%m/%d/', blank=True,
                                       validators=[validate_file_extension, validate_max_file_size]
                                       )

    # A Comment is always related to another model
    # This construction implicitly has property: `on_delete=models.CASCADE`
    content_type = models.ForeignKey(ContentType, help_text=WARNING_TEXT)
    object_id = models.PositiveIntegerField(help_text=WARNING_TEXT)
    content_object = GenericForeignKey()

    nested_comments = GenericRelation('comments.Comment', related_query_name='comments')

    # -- U/S
    # These fields will be removed in the future.
    # They still exists only to prevent possible data loss.
    commentary = models.ForeignKey('commentaries.Commentary', blank=True, null=True,
                                   on_delete=models.CASCADE, help_text=US_NOTICE)
    submission = models.ForeignKey('submissions.Submission', blank=True, null=True,
                                   on_delete=models.CASCADE, related_name='comments_old',
                                   help_text=US_NOTICE)
    thesislink = models.ForeignKey('theses.ThesisLink', blank=True, null=True,
                                   on_delete=models.CASCADE, help_text=US_NOTICE)
    in_reply_to_comment = models.ForeignKey('self', blank=True, null=True,
                                            related_name="nested_comments_old",
                                            on_delete=models.CASCADE, help_text=US_NOTICE)
    in_reply_to_report = models.ForeignKey('submissions.Report', blank=True, null=True,
                                           on_delete=models.CASCADE, help_text=US_NOTICE)
    # -- End U/S

    # Author info
    is_author_reply = models.BooleanField(default=False)
    author = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                               related_name='comments')
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
    remarks_for_editors = models.TextField(blank=True,
                                           verbose_name='optional remarks for the Editors only')
    date_submitted = models.DateTimeField('date submitted', default=timezone.now)
    # Opinions
    nr_A = models.PositiveIntegerField(default=0)
    in_agreement = models.ManyToManyField('scipost.Contributor', related_name='in_agreement',
                                          blank=True)
    nr_N = models.PositiveIntegerField(default=0)
    in_notsure = models.ManyToManyField('scipost.Contributor', related_name='in_notsure',
                                        blank=True)
    nr_D = models.PositiveIntegerField(default=0)
    in_disagreement = models.ManyToManyField('scipost.Contributor', related_name='in_disagreement',
                                             blank=True)

    needs_doi = models.NullBooleanField(default=None)
    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation('journals.GenericDOIDeposit',
                                        related_query_name='genericdoideposit')
    doi_label = models.CharField(max_length=200, blank=True)
    objects = CommentQuerySet.as_manager()

    class Meta:
        permissions = (
            ('can_vet_comments', 'Can vet submitted Comments'),
        )

    def __str__(self):
        return ('by ' + self.author.user.first_name + ' ' + self.author.user.last_name +
                ' on ' + self.date_submitted.strftime('%Y-%m-%d') + ', ' + self.comment_text[:30])

    @property
    def title(self):
        """
        This property is (mainly) used to let Comments get the title of the Submission without
        annoying logic.
        """
        try:
            return self.content_object.title
        except:
            return self.content_type

    @cached_property
    def core_content_object(self):
        # Import here due to circular import errors
        from commentaries.models import Commentary
        from submissions.models import Submission, Report
        from theses.models import ThesisLink

        to_object = self.content_object
        while True:
            if (isinstance(to_object, Submission) or isinstance(to_object, Commentary) or
               isinstance(to_object, ThesisLink)):
                return to_object
            elif isinstance(to_object, Report):
                return to_object.submission
            elif isinstance(to_object, Comment):
                # Nested Comment.
                to_object = to_object.content_object
            else:
                raise Exception

    def create_doi_label(self):
        self.doi_label = 'SciPost.Comment.' + str(self.id)
        self.save()

    @property
    def doi_string(self):
        if self.doi_label:
            return '10.21468/' + self.doi_label
        else:
            return None

    def get_absolute_url(self):
        return self.content_object.get_absolute_url().split('#')[0] + '#comment_id' + str(self.id)

    def get_attachment_url(self):
        return reverse('comments:attachment', args=(self.id,))

    def grant_permissions(self):
        # Import here due to circular import errors
        from submissions.models import Submission

        to_object = self.core_content_object
        if isinstance(to_object, Submission):
            # Add permissions for EIC only, the Vetting-group already has it!
            assign_perm('comments.can_vet_comments', to_object.editor_in_charge.user, self)

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
