__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from comments.factories import CommentaryCommentFactory,\
                               ThesislinkCommentFactory, ReplyCommentFactory


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--comments',
            action='store_true',
            dest='comments',
            default=False,
            help='Add 10 Comments',
        )

    def handle(self, *args, **kwargs):
        if kwargs['comments']:
            self.create_comments()

    def create_comments(self):
        CommentaryCommentFactory.create_batch(3)
        ReplyCommentFactory.create_batch(2)
        ThesislinkCommentFactory.create_batch(3)
        self.stdout.write(self.style.SUCCESS('Successfully created 10 Comments.'))
