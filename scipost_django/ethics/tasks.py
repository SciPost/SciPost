__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime

from SciPost_v1.celery import app

from ethics.models import CoauthoredWork, Coauthorship, PreprintServer
from profiles.models import Profile
from submissions.models.submission import Submission

from typing import Any, Sequence


def fetch_potential_coauthorships_for_profiles_from_preprint_server(
    profile_id: int,
    coauthor_id: int,
    preprint_server_source: str,
    **kwargs: dict[str, Any],
):
    nr_total_works_found = 0
    nr_works_matching_all = 0
    nr_coauthorships_created = 0

    if profile_id == coauthor_id:
        return {
            "nr_total_works_found": 0,
            "nr_works_matching_all": 0,
            "nr_coauthorships_created": 0,
        }

    profile, coauthor = list(Profile.objects.filter(id__in=[profile_id, coauthor_id]))
    # Maintain consistent ordering to avoid duplicates
    if profile.id > coauthor.id:
        profile, coauthor = coauthor, profile

    coauthorships: list[Coauthorship] = []
    preprint_server = PreprintServer.from_name(preprint_server_source)
    five_years_ago = datetime.date.today() - datetime.timedelta(days=5 * 365)

    found_works = preprint_server.server_class.find_common_works_between(
        profile,
        coauthor,
        published_after=five_years_ago,
        **kwargs,
    )
    nr_total_works_found += len(found_works)

    # By using `update_conflicts` any rows failing uniqueness will be retrieved
    # and updated with the newly fetched values. The function returns them such that
    # Coauthorships can be created for them in the next step.
    works = CoauthoredWork.objects.bulk_create(
        found_works,
        update_conflicts=True,
        update_fields=[
            "work_type",
            "title",
            "authors_str",
            "date_updated",
            "date_published",
            "metadata",
        ],
        unique_fields=["server_source", "identifier"],
    )

    coauthorships.extend(
        Coauthorship(work=work, profile=profile, coauthor=coauthor)
        for work in works
        if work.pk is not None  # Make sure works were created successfully
        and work.contains_authors(profile, coauthor)
    )

    nr_works_matching_all = len(coauthorships)
    #! Will have conflicts if the work is already linked to the profiles,
    #! so double check it works as intended
    coauthorships = Coauthorship.objects.bulk_create(
        coauthorships, ignore_conflicts=True
    )
    nr_coauthorships_created = len(list(c for c in coauthorships if c.pk is not None))
    return {
        "nr_total_works_found": nr_total_works_found,
        "nr_works_matching_all": nr_works_matching_all,
        "nr_coauthorships_created": nr_coauthorships_created,
    }


@app.task(bind=True)
def celery_fetch_potential_coauthorships_for_profile_and_submission_authors(
    self,
    profile_id: int,
    submission_id: int,
    preprint_servers: Sequence[str] | None = None,
    **kwargs: dict[str, Any],
):
    submission = Submission.objects.get(id=submission_id)
    submission_authors = list(submission.author_profiles.all())
    preprint_servers = preprint_servers or list(PreprintServer._member_map_.keys())

    nr_total_pairs = len(submission_authors) * len(preprint_servers)
    nr_pairs_checked = 0

    results: dict[str, int] = {}

    if nr_total_pairs == 0:
        raise ValueError("No submission authors or preprint servers to check.")

    for coauthor in submission_authors:
        if coauthor.profile is None:
            raise ValueError(f"Submission author {coauthor} has no linked profile.")

        for preprint_server in preprint_servers:
            result = fetch_potential_coauthorships_for_profiles_from_preprint_server(
                profile_id,
                coauthor.profile.pk,
                preprint_server,
                **kwargs,
            )

            for k, v in result.items():
                results.setdefault(k, 0)
                results[k] += v

            nr_pairs_checked += 1
            self.update_state(
                state="PROGRESS",
                meta={"progress": round(nr_pairs_checked / nr_total_pairs, 3)},
            )

    return results


@app.task(bind=True)
def celery_fetch_potential_coauthorships_between_profiles(
    self,
    profile_id: int,
    coauthor_id: int,
    preprint_servers: Sequence[str] | None = None,
    **kwargs: dict[str, Any],
) -> dict[str, int]:
    preprint_servers = preprint_servers or list(PreprintServer._member_map_.keys())

    results: dict[str, int] = {}
    for i, preprint_server in enumerate(preprint_servers, 1):
        result = fetch_potential_coauthorships_for_profiles_from_preprint_server(
            profile_id,
            coauthor_id,
            preprint_server,
            **kwargs,
        )

        for k, v in result.items():
            results.setdefault(k, 0)
            results[k] += v

        self.update_state(
            state="PROGRESS",
            meta={"progress": int(i / len(preprint_servers))},
        )

    return results
