__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from itertools import zip_longest
from django.core.management.base import BaseCommand
from common.utils import remove_extra_spacing

from submissions.models.submission import Submission


class Command(BaseCommand):
    help = "Clean up multiple spaces in submission fields"
    fields = ["title", "abstract"]

    def handle(self, *args, **options):
        counter = dict(zip(self.fields, [0] * len(self.fields)))

        for submission in Submission.objects.all():
            publications = submission.publications.all()

            for field in self.fields:
                if (value := getattr(submission, field, None)) is None:
                    continue

                cleaned_value = remove_extra_spacing(value)
                if value != cleaned_value:
                    counter[field] += 1
                    setattr(submission, field, cleaned_value)
                    submission.save()

                    # Also update the same field in all publications
                    # stemming from this submission
                    for publication in publications:
                        cleaned_pub_field = remove_extra_spacing(
                            getattr(publication, field, None)
                        )
                        setattr(publication, field, cleaned_pub_field)
                        publication.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleaned up multiple spaces in "
                + ", ".join(list(map(lambda x: f"{counter[x]} {x}s", self.fields)))
            )
        )
