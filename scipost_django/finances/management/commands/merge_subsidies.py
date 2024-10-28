__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from finances.models.subsidy import Subsidy
from pins.models import Note

SUBSIDY_CONTENT_TYPE = ContentType.objects.get_for_model(Subsidy)


def merge_subsidies(subsidy_ids: list[int]) -> Subsidy:
    subsidies = Subsidy.objects.filter(id__in=subsidy_ids).order_by("id")

    if not subsidies.exists():
        raise ValueError("No subsidies found with the given IDs")

    subsidies = subsidies.order_by("id")
    main_subsidy: Subsidy = subsidies.first()
    other_subsidies = subsidies[1:]

    if not all(
        subsidy.organization == main_subsidy.organization for subsidy in other_subsidies
    ):
        raise ValueError("All subsidies must belong to the same organization.")

    main_subsidy.date_from = min(subsidy.date_from for subsidy in subsidies)
    main_subsidy.date_until = max(subsidy.date_until for subsidy in subsidies)
    for other_subsidy in other_subsidies:

        other_subsidy.attachments.update(subsidy=main_subsidy)
        other_subsidy.payments.update(subsidy=main_subsidy)
        other_subsidy.compensated_pubfracs.update(compensated_by=main_subsidy)

        Note.objects.filter(
            regarding_content_type=SUBSIDY_CONTENT_TYPE,
            regarding_object_id=other_subsidy.id,
        ).update(
            regarding_content_type=SUBSIDY_CONTENT_TYPE,
            regarding_object_id=main_subsidy.id,
        )

        main_subsidy.status = other_subsidy.status or main_subsidy.status
        main_subsidy.paid_on = other_subsidy.paid_on or main_subsidy.paid_on
        main_subsidy.description += "\n" + other_subsidy.description
        main_subsidy.amount += other_subsidy.amount

        main_subsidy.save()
        other_subsidy.delete()

    return main_subsidy


class Command(BaseCommand):
    help = "Merge the subsidies with the given IDs into a single subsidy"

    def add_arguments(self, parser):
        parser.add_argument("subsidy_ids", nargs="+", type=int)

    def handle(self, *args, **kwargs):
        subsidy_ids = kwargs["subsidy_ids"]
        main_subsidy = merge_subsidies(subsidy_ids)
        self.stdout.write(
            f"Merged subsidies {subsidy_ids} into {main_subsidy.id} ({main_subsidy})"
        )
