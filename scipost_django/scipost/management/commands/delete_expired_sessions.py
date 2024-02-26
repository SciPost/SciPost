__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
from django.core.management.base import BaseCommand
from django.utils.timezone import datetime, now


class Command(BaseCommand):
    help = "Delete expired sessions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--expiration_date",
            type=str,
            required=False,
            default=now().strftime("%Y-%m-%d"),
            help="Expiration date before which to delete sessions (format: YYYY-MM-DD)",
        )

    def handle(self, *args, **kwargs):
        if re.match(r"^\d{4}-\d{2}-\d{2}$", kwargs["expiration_date"]):
            expiration_date = datetime.strptime(
                kwargs["expiration_date"], "%Y-%m-%d"
            ).astimezone()
            self.delete_expired_sessions(expiration_date)

        else:
            raise ValueError(
                "Invalid expiration date format. Please use the format YYYY-MM-DD."
            )

    def delete_expired_sessions(self, expiration_date: datetime):
        from django.contrib.sessions.models import Session

        sessions_to_delete = Session.objects.filter(expire_date__lt=expiration_date)
        sessions_count = sessions_to_delete.count()
        sessions_to_delete.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {sessions_count} "
                f"expired sessions before {expiration_date.date()}."
            )
        )
