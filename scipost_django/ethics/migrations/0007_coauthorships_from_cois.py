from django.db import migrations

from django.db.models.functions import Substr
from django.db.models import F, Q, Exists, OuterRef, Subquery


def migrate_cois_to_coauthorships(apps, schema_editor):
    try:
        ConflictOfInterest = apps.get_model("conflicts", "ConflictOfInterest")
        Coauthorship = apps.get_model("ethics", "Coauthorship")
        CoauthoredWork = apps.get_model("ethics", "CoauthoredWork")
    except LookupError:
        return

    cois = ConflictOfInterest.objects.annotate(
        same_author=Q(profile__id=F("related_profile__id")),
        identifier=Substr(F("url"), len("https://arxiv.org/abs/") + 1, None),
    )

    # Properly order profile and coauthor to avoid duplicates
    cois.annotate(
        should_reverse_author_order=Q(profile__id__gt=F("related_profile__id"))
    ).filter(should_reverse_author_order=True).update(
        profile=F("related_profile"), related_profile=F("profile")
    )

    # Maintain verified status by cross-copying across potential duplicates
    cois.annotate(
        is_any_verified=Exists(
            ConflictOfInterest.objects.filter(
                Q(profile=OuterRef("related_profile")) | Q(profile=OuterRef("profile")),
                Q(related_profile=OuterRef("related_profile"))
                | Q(related_profile=OuterRef("profile")),
                url=OuterRef("url"),
                status="verified",
            )
        )
    ).filter(is_any_verified=True).update(status="verified")

    # Create CoauthoredWorks from distinct identifiers
    works = [
        CoauthoredWork(
            server_source="arxiv",
            work_type="preprint",
            identifier=coi.identifier,
            title=coi.header,
            authors_str="",
            date_published=coi.resource_date,
            date_fetched=coi.created,
        )
        for coi in cois.filter(same_author=False)
        .order_by("identifier", "created")
        .distinct("identifier")
    ]
    works = CoauthoredWork.objects.bulk_create(works)
    mapped_works = {work.identifier: work.id for work in works}

    # Create Coauthorships from ConflictOfInterests, keeping the older date in each
    # potential duplicate pair
    coauthorships = [
        Coauthorship(
            profile=coi.profile,
            coauthor=coi.related_profile,
            work_id=mapped_works.get(coi.identifier),
            status=coi.status,
            created=coi.older_created,
            modified=coi.older_modified,
        )
        for coi in cois.annotate(
            older_created=Subquery(
                ConflictOfInterest.objects.filter(
                    Q(profile=OuterRef("related_profile"))
                    | Q(profile=OuterRef("profile")),
                    Q(related_profile=OuterRef("related_profile"))
                    | Q(related_profile=OuterRef("profile")),
                    url=OuterRef("url"),
                ).values("created")[:1]
            ),
            older_modified=Subquery(
                ConflictOfInterest.objects.filter(
                    Q(profile=OuterRef("related_profile"))
                    | Q(profile=OuterRef("profile")),
                    Q(related_profile=OuterRef("related_profile"))
                    | Q(related_profile=OuterRef("profile")),
                    url=OuterRef("url"),
                ).values("modified")[:1]
            ),
        ).filter(same_author=False)
    ]
    coauthorships = Coauthorship.objects.bulk_create(coauthorships)

    # Remove any duplicate Coauthorships that are still lingering
    # prefering those with verified status and older created date
    Coauthorship.objects.exclude(
        id__in=Coauthorship.objects.all()
        .order_by("profile_id", "coauthor_id", "work_id", "status", "created")
        .distinct("profile_id", "coauthor_id", "work_id")
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ethics", "0006_coauthoredwork_coauthorship"),
    ]

    operations = [
        migrations.RunPython(
            migrate_cois_to_coauthorships,
            reverse_code=migrations.RunPython.noop,
        )
    ]
