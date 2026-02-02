__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from django.db.models import Q, Count
from django.db.models.functions import ExtractYear

from common.utils import BaseMailUtil, get_current_domain
from common.utils.dates import date_to_str, is_date_representation

domain = get_current_domain()

if TYPE_CHECKING:
    from scipost.models import Contributor
    from django.db.models.query import ValuesQuerySet


def build_absolute_uri_using_site(path):
    """
    In cases where request is not available, build absolute uri from Sites framework.
    """
    return "https://{domain}{path}".format(domain=domain, path=path)


SCIPOST_SUMMARY_FOOTER = (
    "\n\n--------------------------------------------------"
    "\n\nAbout SciPost:\n\n"
    "SciPost.org is a publication portal managed by "
    "professional scientists, offering (among others) high-quality "
    "two-way open access journals (free to read, free to publish in) "
    "with an innovative peer-witnessed form of refereeing. "
    "The site also offers a Commentaries section, providing a "
    "means of commenting on all existing literature. SciPost is established as "
    "a not-for-profit foundation devoted to serving the interests of the "
    "international scientific community."
    f"\n\nThe site is anchored at https://{domain}. Many further details "
    "about SciPost, its principles, ideals and implementation can be found at "
    f"https://{domain}/about and https://{domain}/FAQ.\n"
    f"Professional scientists can register at https://{domain}/register."
)

SCIPOST_SUMMARY_FOOTER_HTML = (
    "\n<br/><br/>--------------------------------------------------"
    "<br/><p>About SciPost:</p>"
    "<p>SciPost.org is a publication portal managed by "
    "professional scientists, offering (among others) high-quality "
    "two-way open access journals (free to read, free to publish in) "
    "with an innovative peer-witnessed form of refereeing. "
    "The site also offers a Commentaries section, providing a "
    "means of commenting on all existing literature. SciPost is established as "
    "a not-for-profit foundation devoted to serving the interests of the "
    "international scientific community.</p>"
    f"<p>The site is anchored at https://{domain}. Many further details "
    "about SciPost, its principles, ideals and implementation can be found at "
    f"https://{domain}/about and https://{domain}/FAQ.\n"
    f"Professional scientists can register at https://{domain}/register.</p>"
)


EMAIL_FOOTER = (
    "\n{% load static %}"
    f'<a href="https://{domain}">'
    '<img src="{% static \'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px"></a><br/>'
    '<div style="background-color: #f0f0f0; color: #002B49; align-items: center;">'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/journals/">Journals</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/submissions/">Submissions</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/commentaries/">Commentaries</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/theses/">Theses</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/login/">Login</a></div>'
    "</div>"
)

EMAIL_UNSUBSCRIBE_LINK_PLAIN = (
    "\n\nDon't want to receive such emails? Unsubscribe by "
    f"updating your personal data at https://{domain}/update_personal_data."
)

EMAIL_UNSUBSCRIBE_LINK_HTML = (
    '\n\n<p style="font-size: 10px;">Don\'t want to receive such emails? Unsubscribe by '
    f'<a href="https://{domain}/update_personal_data">updating your personal data</a>.</p>'
)


# Recursive type of dict[str -> dict | int]
TContributorStatDictKey = str | int
TContributorStatDict = dict[TContributorStatDictKey, "TContributorStatDict | int"]


class ContributorStatsAccessor:
    """
    A utility class to access contributor statistics.
    It will implement methods to retrieve various statistics,
    aggregating live data and historical anonymized data from the Contributor model.
    This class is intended to be used as a property of the Contributor model,
    and as the sole interface for accessing contributor statistics.
    """

    def __init__(self, contributor: "Contributor") -> None:
        self.contributor = contributor
        self._deltas: TContributorStatDict = {}

    @property
    def stats(self) -> TContributorStatDict:
        """
        Combine the contributor's anonymous statistics with any deltas
        and return the result as a nested dictionary.
        """
        # If deltas are empty, return the anonymous stats directly
        if not self._deltas:
            return self.contributor.anonymous_stats

        stats = self.contributor.anonymous_stats.copy()

        # Merge deltas into the initial stats
        def _merge_deltas(
            d: TContributorStatDict,
            deltas: TContributorStatDict,
        ) -> None:
            for key, value in deltas.items():
                if isinstance(value, dict):
                    # If the value is a dict, recurse into it
                    _merge_deltas(d.setdefault(key, {}), value)
                else:
                    # Otherwise, set the value directly
                    d[key] = d.get(key, 0) + value

        _merge_deltas(stats, self._deltas)
        return stats

    def increment_anon(
        self,
        *keys: TContributorStatDictKey | date | datetime,
        by: int = 1,
        subgroup: TContributorStatDictKey | None = None,
    ) -> None:
        """
        Increment the contributor's statistics for the given keys (as a nested dict).
        The keys are expected to be in the form of a path, e.g. "nr_assignments_completed", "monthly", "2023-10-01".
        Stats are retrieved from the Contributor object lazily and will be committed at the end of the command.

        If a subgroup is provided, it will increment both the subgroup and a "total" key.
        This is useful for aggregating statistics across different subgroups, such as years or months.
        """
        if self.contributor.is_anonymous:
            return

        def _increment(
            d: TContributorStatDict,
            *keys: TContributorStatDictKey | date | datetime,
        ) -> None:
            key, *rest_keys = keys

            # Cast date to string
            key = date_to_str(key) if is_date_representation(key) else str(key)

            if not rest_keys:
                d.setdefault(key, 0)
                # d[key] is always int if rest_keys is empty
                d[key] += by  # type: ignore
            else:
                d.setdefault(key, {})
                # d[key] is always a dict if rest_keys is not empty
                _increment(d[key], *rest_keys)  # type: ignore

        # If a subgroup is provided, we assume the keys are leading up to the subgroup's parent
        # We then increment both the subgroup and a "total" key
        if subgroup:
            _increment(self._deltas, *keys, subgroup)
            _increment(self._deltas, *keys, "total")
        else:
            _increment(self._deltas, *keys)

    def clear_deltas(self) -> None:
        """
        Reset the deltas dictionary to an empty state.
        """
        self._deltas = {}

    def save(self) -> None:
        """
        Save the contributor's statistics to the database by merging the deltas
        with the existing anonymous stats. This will update the contributor's
        anonymous_stats field with the new values.
        """
        self.contributor.anonymous_stats = self.stats
        self.contributor.save(update_fields=["anonymous_stats"])
        self.clear_deltas()

    # Define the retrieval functions that will be used to access the statistics.
    def _merge_stats(
        self,
        epon_qs: "ValuesQuerySet[Any, Any]",
        anon_stat_keys: tuple[TContributorStatDictKey, ...],
    ) -> TContributorStatDict:
        """
        Merge eponymous stats from the queryset with anonymous stats from the contributor.
        Returns a dictionary with the total counts for each key.

        Eponymous stats are expected to be in the form of a ValuesQuerySet,
        where the first element is the subgroup key and the second element is the count.
        Anonymous stats are extracted from the provided key path, like in `increment_anon`.
        """
        epon_stats = dict(epon_qs)
        epon_stats["total"] = sum(epon_stats.values())

        anon_stats = self.contributor.anonymous_stats
        for key in anon_stat_keys:
            anon_stats = anon_stats.get(key, {})
            if not isinstance(anon_stats, dict):
                raise TypeError(
                    f"Anonymous stats for {anon_stat_keys} should be a dict, not {type(anon_stats)}."
                )

        # Combine eponymous and anonymous stats
        total_stats = {
            key: epon_stats.get(key, 0) + anon_stats.get(key, 0)
            for key in (set(epon_stats.keys()) | set(anon_stats.keys()))
        }

        return total_stats

    def nr_assignments_completed(self) -> TContributorStatDict:
        from submissions.models.assignment import EditorialAssignment

        completed_assignments_by_year = (
            EditorialAssignment.objects.filter(
                to=self.contributor,
                status=EditorialAssignment.STATUS_COMPLETED,
            )
            .annotate(year=ExtractYear("date_created"))
            .values("year")
            .annotate(count=Count("year"))
            .values_list("year", "count")
        )

        total_stats = self._merge_stats(
            completed_assignments_by_year,
            anon_stat_keys=("nr_assignments_completed",),
        )

        return total_stats

    def nr_recommendations_eligible(self) -> TContributorStatDict:
        from submissions.models.recommendation import EICRecommendation

        epon_stats = (
            EICRecommendation.objects.filter(
                eligible_to_vote=self.contributor,
            )
            .annotate(year=ExtractYear("date_submitted"))
            .values("year")
            .annotate(count=Count("year"))
            .values_list("year", "count")
        )

        total_stats = self._merge_stats(
            epon_stats,
            anon_stat_keys=("nr_recommendations_eligible",),
        )

        return total_stats

    def nr_recommendations_voted(self) -> TContributorStatDict:
        from submissions.models.recommendation import EICRecommendation

        epon_stats = (
            EICRecommendation.objects.filter(
                Q(voted_for=self.contributor)
                | Q(voted_against=self.contributor)
                | Q(voted_abstain=self.contributor),
            )
            .annotate(year=ExtractYear("date_submitted"))
            .values("year")
            .annotate(count=Count("year"))
            .values_list("year", "count")
        )

        total_stats = self._merge_stats(
            epon_stats,
            anon_stat_keys=("nr_recommendations_voted",),
        )

        return total_stats
