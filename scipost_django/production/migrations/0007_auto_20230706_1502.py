# Generated by Django 3.2.18 on 2023-07-06 13:02

from django.db import migrations, models


def add_name_to_repos(apps, schema_editor):
    from common.utils import latinise
    from django.db.models.functions import Concat
    from django.db.models import Value

    ProofsRepository = apps.get_model("production", "ProofsRepository")
    Profile = apps.get_model("profiles", "Profile")

    def _clean_author_list(authors_str: str):
        comma_separated = authors_str.replace(", and", ", ")
        comma_separated = comma_separated.replace(" and ", ", ")
        comma_separated = comma_separated.replace(", & ", ", ")
        comma_separated = comma_separated.replace(" & ", ", ")
        comma_separated = comma_separated.replace(";", ", ")
        return [e.lstrip().rstrip() for e in comma_separated.split(",")]

    def _get_repo_name(stream) -> str:
        """
        Return the name of the repository in the form of "id_lastname".
        """
        # Get the last name of the first author by getting the first author string from the submission
        first_author_str = _clean_author_list(stream.submission.author_list)[0]
        first_author_profile = (
            Profile.objects.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            )
            .filter(full_name=first_author_str)
            .first()
        )
        if first_author_profile is None:
            first_author_last_name = first_author_str.split(" ")[-1]
        else:
            first_author_last_name = first_author_profile.last_name

        # Remove accents from the last name to avoid encoding issues
        # and join multiple last names into one
        first_author_last_name = latinise(first_author_last_name).strip()
        first_author_last_name = first_author_last_name.replace(" ", "-")

        return "{preprint_id}_{last_name}".format(
            preprint_id=stream.submission.preprint.identifier_w_vn_nr,
            last_name=first_author_last_name,
        )

    for repo in ProofsRepository.objects.all():
        repo.name = _get_repo_name(repo.stream)
        repo.save()


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0006_proofsrepository"),
    ]

    operations = [
        migrations.AddField(
            model_name="proofsrepository",
            name="name",
            field=models.CharField(default="", max_length=128),
        ),
        migrations.RunPython(add_name_to_repos, reverse_code=migrations.RunPython.noop),
    ]
