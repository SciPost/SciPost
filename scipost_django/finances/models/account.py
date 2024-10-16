__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import date
import datetime
from typing import TYPE_CHECKING
from django.db import models
from django.utils.functional import cached_property

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from finances.models.balance import Balance
    from finances.models.transaction import FuturePeriodicTransaction


class Account(models.Model):

    name = models.CharField(max_length=128)
    number = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    if TYPE_CHECKING:
        balance_entries: "RelatedManager[Balance]"
        future_transactions: "RelatedManager[FuturePeriodicTransaction]"

    def __str__(self):
        return self.name

    @property
    def balance(self):
        return self.balance_entries.order_by("date").last()

    def projected_balance(self, projection_date: date, smooth=False) -> float:
        """
        Returns the projected balance at a given date, based on the last balance entry
        and FuturePeriodicTransaction entries.

        If smooth is True, the future transactions are distributed evenly over the period
        until the given date instead of being applied at the end of each of their periods.
        """
        balance = float(self.balance.amount if self.balance else 0)

        today = date.today()
        for transaction in self.future_transactions:

            projection_duration_days = (projection_date - today).days
            if projection_duration_days <= 0:
                continue

            periods_until_date = projection_duration_days / transaction.period.days
            if not smooth:
                days_until_next_transaction = transaction.period.days - (
                    (today - transaction.date_from).days % transaction.period.days
                )

                days_past_period = projection_duration_days % transaction.period.days
                triggers_first_transaction = (
                    days_past_period >= days_until_next_transaction
                )
                periods_until_date = int(periods_until_date) + int(
                    triggers_first_transaction
                )

            balance += periods_until_date * float(transaction.amount)

        return balance

    @cached_property
    def zero_balance_projection(self):
        """
        Returns the date at which the balance will be zero. Returns None if the balance
        will never be zero, e.g. if the balance is positive and no future transactions.
        """

        if not self.future_transactions:
            return None

        future_transactions = self.future_transactions.values_list(
            "period", "date_from", "amount"
        ).order_by("date_from")

        # Define linearly changing daily rate ranges by aggregating the future transactions
        # The date specifies the start of the period for which the rate is valid until the next entry
        daily_change: dict[date, float] = {}
        for period, transition_start, amount in future_transactions:
            daily_rate = amount / period.days

            if transition_start not in daily_change:
                daily_change[transition_start] = 0
            daily_change[transition_start] += float(daily_rate)

        balance = float(self.balance.amount if self.balance else 0)

        start_date = datetime.date.today()
        for (rate_start, rate), rate_end in zip(
            daily_change.items(), list(daily_change.keys())[1:] + [datetime.date.max]
        ):
            # Clip the start date to when transactions start if it is before
            if start_date < rate_start:
                start_date = rate_start

            # A root exists only if the daily rate is negative
            if rate < 0:
                zero_date = start_date + datetime.timedelta(days=balance / -rate)

                # Return the first root if it is before the next change in daily rate
                if zero_date < rate_end:
                    return zero_date

            balance += rate * (rate_end - start_date).days
            start_date = rate_start
