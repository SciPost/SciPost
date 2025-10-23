__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandParser
from django.template.loader import render_to_string

from mails.utils import DirectMailUtil
from finances.forms import LogsFilterForm
from finances.models.work_log import HOURLY_RATE


class Command(BaseCommand):
    """
    This command handles the creation and updating of git repositories.
    """

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--start",
            type=str,
            required=False,
            help="The start date for the worklogs to be considered, in the format 'YYYY-MM-DD'.",
        )

        parser.add_argument(
            "--end",
            type=str,
            required=False,
            help="The end date for the worklogs to be considered, in the format 'YYYY-MM-DD'.",
        )

        parser.add_argument(
            "--hourly_rate",
            type=float,
            required=False,
            help="The hourly rate to be used for the worklogs.",
        )

    def handle(self, *args, **options):
        current_month = datetime.date.today().replace(day=1)
        last_month_end = current_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        start = options["start"] or last_month_start.strftime("%Y-%m-%d")
        end = options["end"] or last_month_end.strftime("%Y-%m-%d")
        form = LogsFilterForm(
            {
                "hourly_rate": options["hourly_rate"] or HOURLY_RATE,
                "start": datetime.datetime.strptime(start, "%Y-%m-%d"),
                "end": datetime.datetime.strptime(end, "%Y-%m-%d"),
            }
        )

        if not form.is_valid():
            self.stderr.write("Invalid form data.")
            return

        rendered_table = render_to_string(
            "finances/_worklog_summary_table.html",
            {
                "logs_filter_form": form,
            },
        )

        mail_request = DirectMailUtil(
            "careers/worklogs_report",
            rendered_table=rendered_table,
            start=start,
            end=end,
            group=Group.objects.get(name="Human Resources Administrators"),
        )
        mail_request.send_mail()

        self.stdout.write("Worklogs report sent to HR.")
