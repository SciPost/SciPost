__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime
import itertools

from celery import chord, group

from SciPost_v1.celery import app
from common.utils.db import postgres_lock

from ethics.models import CoauthoredWork, Coauthorship, PreprintServer
from preprints.servers.server import BasePreprintServer
from profiles.models import Profile
from submissions.models.submission import Submission

from typing import Any, Iterable

# Set a max number of authors to consider for a work to be saved.
# Processing coauthorships for works of many authors is taxing to EdAdmin
# and any CoIs would be likely exempted anyway.
MAX_AUTHORS_TO_CONSIDER_COIS = 20


PREPRINT_SERVER_CLASS_INSTANCES = {
    name: klass() for name, klass in PreprintServer.mapping().items()
}


def query_coauthorships(
    author: Profile,
    coauthor: Profile,
    preprint_server: BasePreprintServer,
    **kwargs: dict[str, Any],
):
    nr_total_works_found = 0
    nr_works_matching_all = 0
    nr_coauthorships_created = 0

    if author == coauthor:
        return {
            "nr_total_works_found": 0,
            "nr_works_matching_all": 0,
            "nr_coauthorships_created": 0,
        }

    # Maintain consistent ordering to avoid duplicates
    if author.id > coauthor.id:
        author, coauthor = coauthor, author

    coauthorships_to_create: list[Coauthorship] = []
    five_years_ago = datetime.date.today() - datetime.timedelta(days=5 * 365)

    found_works = preprint_server.find_common_works_between(
        author,
        coauthor,
        published_after=five_years_ago,
        **kwargs,
    )
    found_works.sort(key=lambda w: (w.server_source, w.identifier))
    nr_total_works_found += len(found_works)

    works_to_create = [
        work
        for work in found_works
        if work.nr_authors <= MAX_AUTHORS_TO_CONSIDER_COIS
        and work.contains_authors(author, coauthor)
    ]

    # Use a lock to avoid race conditions when upserting works
    with postgres_lock(
        f"celery_fetch_potential_coauthorships_coauthored_works_{preprint_server.name}",
        max_retries=20,
        retry_delay=0.5,
    ):
        # By using `update_conflicts` any rows failing uniqueness will be retrieved
        # and updated with the newly fetched values. The function returns them such that
        # Coauthorships can be created for them in the next step.
        works_created = CoauthoredWork.objects.bulk_create(
            works_to_create,
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

    coauthorships_to_create.extend(
        Coauthorship(work=work, profile=author, coauthor=coauthor)
        for work in works_created
        if work.pk is not None  # Make sure works were created successfully
    )

    nr_works_matching_all = len(coauthorships_to_create)
    #! Will have conflicts if the work is already linked to the profiles,
    #! so double check it works as intended
    coauthorships_created = Coauthorship.objects.bulk_create(
        coauthorships_to_create, ignore_conflicts=True
    )
    nr_coauthorships_created = len(
        list(c for c in coauthorships_created if c.pk is not None)
    )
    return {
        "nr_total_works_found": nr_total_works_found,
        "nr_works_matching_all": nr_works_matching_all,
        "nr_coauthorships_created": nr_coauthorships_created,
    }


@app.task(bind=True, trail=True)
def task_query_coauthorships_in_server(
    self,
    author_ids: Iterable[int],
    coauthor_ids: Iterable[int],
    preprint_server_name: str,
):

    try:
        preprint_server_class = PREPRINT_SERVER_CLASS_INSTANCES[preprint_server_name]
    except KeyError:
        raise ValueError(f"Invalid preprint server: {preprint_server_name}")

    profiles = {
        p.id: p
        for p in Profile.objects.filter(
            id__in=itertools.chain(author_ids, coauthor_ids)
        ).order_by("id")
    }

    authors = [p for author_id in author_ids if (p := profiles.get(author_id))]
    coauthors = [p for coauthor_id in coauthor_ids if (p := profiles.get(coauthor_id))]

    profile_pairs = list(itertools.product(authors, coauthors))
    total_pairs = len(profile_pairs)

    results: list[dict[str, int]] = []
    for i, (author, coauthor) in enumerate(profile_pairs):
        self.update_state(
            state="PROGRESS",
            meta={
                "current": f"({author.id}, {coauthor.id})",
                "progress": round(i / total_pairs, 3),
                "total": total_pairs,
            },
        )
        result = query_coauthorships(
            author=author,
            coauthor=coauthor,
            preprint_server=preprint_server_class,
        )
        results.append(result)

    return {
        key: sum(result.get(key, 0) for result in results)
        for key in [
            "nr_total_works_found",
            "nr_works_matching_all",
            "nr_coauthorships_created",
        ]
    }


def query_submission_authors_coauthorships_against_profile(
    profile_id: int,
    submission_id: int,
    **kwargs: dict[str, Any],
):
    submission = Submission.objects.get(id=submission_id)
    preprint_server_names = submission.get_coauthorship_preprint_servers()

    submission_author_ids = list(
        submission.author_profiles.all()
        .order_by("profile_id")
        .values_list("profile_id", flat=True)
    )
    nr_total_pairs = len(submission_author_ids) * len(preprint_server_names)
    if nr_total_pairs == 0:
        raise ValueError("No submission authors or preprint servers to check.")

    # Run parallel tasks for each preprint server
    group_task = group(
        task_query_coauthorships_in_server.s(
            submission_author_ids,
            [profile_id],
            server_name,
        )
        for server_name in preprint_server_names
    )

    return group_task


def query_submission_authors_fellows_coauthorships(submission_id: int):
    submission = Submission.objects.get(id=submission_id)
    preprint_server_names = submission.get_coauthorship_preprint_servers()

    submission_authors_ids = list(
        submission.author_profiles.all()
        .order_by("profile_id")
        .values_list("profile_id", flat=True)
    )
    fellowship_ids = list(
        submission.fellows.all()
        .order_by("contributor__profile_id")
        .values_list("contributor__profile_id", flat=True)
    )

    nr_total_pairs = len(submission_authors_ids) * len(fellowship_ids)
    if nr_total_pairs == 0:
        raise ValueError("No submission authors or fellows to check.")

    chord_task = chord(
        group(
            task_query_coauthorships_in_server.si(
                submission_authors_ids,
                fellowship_ids,
                server_name,
            )
            for server_name in preprint_server_names
        ),
        handle_successful_coauthorship_updates.s(submission.id),
    ).on_error(handle_failed_coauthorship_updates.si(submission.id))

    return chord_task


@app.task(bind=True, trail=True)
def handle_successful_coauthorship_updates(
    self, results: list[dict[str, int]], submission_id: int
):
    submission = Submission.objects.get(id=submission_id)
    submission.needs_coauthorships_update = False
    submission.save()

    return {
        key: sum(result.get(key, 0) for result in results)
        for key in [
            "nr_total_works_found",
            "nr_works_matching_all",
            "nr_coauthorships_created",
        ]
    }


@app.task(bind=True, trail=True)
def handle_failed_coauthorship_updates(self, submission_id: int):
    submission = Submission.objects.get(id=submission_id)
    submission.needs_coauthorships_update = True
    submission.save()
