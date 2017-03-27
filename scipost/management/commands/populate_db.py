from django.core.management.base import BaseCommand

from news.factories import NewsItemFactory

from ...factories import ContributorFactory, EditorialCollegeFactory, EditorialCollegeFellowshipFactory


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
            '--contributor',
            action='store_true',
            dest='contributor',
            default=False,
            help='Add Contributors',
        )
        parser.add_argument(
            '--college',
            action='store_true',
            dest='editorial-college',
            default=False,
            help='Add Editorial College and Fellows (Contributors required)',
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
            self.create_contributors()
        if kwargs['editorial-college'] or kwargs['all']:
            self.create_editorial_college()
            self.create_editorial_college_fellows()
        if kwargs['news'] or kwargs['all']:
            self.create_news_items()

    def create_contributors(self):
        ContributorFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created Contributors.'))

    def create_editorial_college(self):
        EditorialCollegeFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College\'s.'))

    def create_editorial_college_fellows(self):
        EditorialCollegeFellowshipFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College Fellows.'))

    def create_news_items(self):
        NewsItemFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created News items.'))
