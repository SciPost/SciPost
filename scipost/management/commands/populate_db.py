from django.core.management.base import BaseCommand

from commentaries.factories import VettedCommentaryFactory
from comments.factories import CommentaryCommentFactory, SubmissionCommentFactory,\
                               ThesislinkCommentFactory
from scipost.factories import SubmissionRemarkFactory
from journals.factories import JournalFactory, VolumeFactory, IssueFactory, PublicationFactory
from news.factories import NewsItemFactory
from submissions.factories import EICassignedSubmissionFactory
from theses.factories import VettedThesisLinkFactory

from ...factories import ContributorFactory, EditorialCollegeFactory,\
                         EditorialCollegeFellowshipFactory


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--news',
            action='store_true',
            dest='news',
            default=False,
            help='Add NewsItems',
        )
        parser.add_argument(
            '--commentaries',
            action='store_true',
            dest='commentaries',
            default=False,
            help='Add 5 Commentaries',
        )
        parser.add_argument(
            '--comments',
            action='store_true',
            dest='comments',
            default=False,
            help='Add 10 Comments',
        )
        parser.add_argument(
            '--contributor',
            action='store_true',
            dest='contributor',
            default=False,
            help='Add 5 Contributors',
        )
        parser.add_argument(
            '--college',
            action='store_true',
            dest='editorial-college',
            default=False,
            help='Add 5 Editorial College and Fellows (Contributors required)',
        )
        parser.add_argument(
            '--pubset',
            action='store_true',
            dest='pubset',
            default=False,
            help='Add 5 Issues, Volumes and Journals',
        )
        parser.add_argument(
            '--issues',
            action='store_true',
            dest='issues',
            default=False,
            help='Add 5 Issues',
        )
        parser.add_argument(
            '--submissions',
            action='store_true',
            dest='submissions',
            default=False,
            help='Add 5 new submissions status EIC assigned',
        )
        parser.add_argument(
            '--publications',
            action='store_true',
            dest='publications',
            default=False,
            help='Add 5 Publications (includes --issues action)',
        )
        parser.add_argument(
            '--remarks',
            action='store_true',
            dest='remarks',
            default=False,
            help='Add 5 new Remarks linked to Submissions',
        )
        parser.add_argument(
            '--theses',
            action='store_true',
            dest='theses',
            default=False,
            help='Add 5 ThesisLinks',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Add all available',
        )

    def handle(self, *args, **kwargs):
        if kwargs['contributor'] or kwargs['all']:
            n = 5
            if kwargs['all']:
                n += 10
            self.create_contributors(n)
        if kwargs['commentaries'] or kwargs['all']:
            self.create_commentaries()
        if kwargs['comments'] or kwargs['all']:
            self.create_comments()
        if kwargs['editorial-college'] or kwargs['all']:
            self.create_editorial_college()
            self.create_editorial_college_fellows()
        if kwargs['news'] or kwargs['all']:
            self.create_news_items()
        if kwargs['submissions'] or kwargs['all']:
            self.create_submissions()
        if kwargs['pubset'] or kwargs['all']:
            self.create_pubset()
        if kwargs['issues'] or kwargs['all']:
            self.create_issues()
        if kwargs['publications'] or kwargs['all']:
            self.create_publications()
        if kwargs['remarks'] or kwargs['all']:
            self.create_remarks()
        if kwargs['theses'] or kwargs['all']:
            self.create_theses()

    def create_contributors(self, n=5):
        ContributorFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created %i Contributors.' % n))

    def create_commentaries(self):
        VettedCommentaryFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Commentaries.'))

    def create_comments(self):
        CommentaryCommentFactory.create_batch(3)
        SubmissionCommentFactory.create_batch(4)
        ThesislinkCommentFactory.create_batch(3)
        self.stdout.write(self.style.SUCCESS('Successfully created 10 Comments.'))

    def create_editorial_college(self):
        EditorialCollegeFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Editorial College\'s.'))

    def create_editorial_college_fellows(self):
        EditorialCollegeFellowshipFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Editorial College Fellows.'))

    def create_news_items(self):
        NewsItemFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 News items.'))

    def create_submissions(self):
        EICassignedSubmissionFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Submissions.'))

    def create_pubset(self):
        VolumeFactory.create_batch(5)
        IssueFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS(
                          'Successfully created 5x {Journal, Volume and Issue}.'))

    def create_issues(self):
        IssueFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS(
                          'Successfully created 5 Issue.'))

    def create_publications(self):
        PublicationFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Publications.'))

    def create_remarks(self):
        SubmissionRemarkFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 Remarks.'))

    def create_theses(self):
        VettedThesisLinkFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created 5 ThesisLinks.'))
