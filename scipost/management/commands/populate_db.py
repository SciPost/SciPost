from django.core.management.base import BaseCommand

from news.factories import NewsItemFactory

from ...factories import EditorialCollegeFactory, EditorialCollegeMemberFactory


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
            '--editorial-college',
            action='store_true',
            dest='editorial-college',
            default=False,
            help='Add Editorial College and members',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Add all available',
        )

    def handle(self, *args, **kwargs):
        if kwargs['editorial-college'] or kwargs['all']:
            self.create_editorial_college()
            self.create_editorial_college_members()
        if kwargs['news'] or kwargs['all']:
            self.create_news_items()

    def create_editorial_college(self):
        EditorialCollegeFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College\'s.'))

    def create_editorial_college_members(self):
        EditorialCollegeMemberFactory.create_batch(20)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College Members.'))

    def create_news_items(self):
        NewsItemFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created News items.'))
