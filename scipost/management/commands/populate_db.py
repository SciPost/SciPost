from django.core.management.base import BaseCommand

from ...factories import EditorialCollegeFactory, EditorialCollegeMemberFactory


class Command(BaseCommand):
    def create_editorial_college(self):
        EditorialCollegeFactory.create_batch(5)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College\'s.'))

    def create_editorial_college_members(self):
        EditorialCollegeMemberFactory.create_batch(20)
        self.stdout.write(self.style.SUCCESS('Successfully created Editorial College Members.'))

    def handle(self, *args, **kwargs):
        self.create_editorial_college()
        self.create_editorial_college_members()
