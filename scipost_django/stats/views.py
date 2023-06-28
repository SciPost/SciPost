__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from journals.models import Journal, Volume, Issue, Publication, PublicationAuthorsTable
from submissions.models import Submission


def country_level_authorships(request):
    context = {}
    context["countrycodes"] = list(
        set(
            [
                item["authors__affiliations__country"]
                for item in list(
                    Publication.objects.all().values("authors__affiliations__country")
                )
                if item["authors__affiliations__country"]
            ]
        )
    )
    context["countrycodes"].sort()
    return render(request, "stats/country_level_authorships.html", context)


def _hx_country_level_authorships(request, country):
    publications = Publication.objects.filter(
        authors__affiliations__country=country
    ).distinct()
    authorships = PublicationAuthorsTable.objects.filter(affiliations__country=country)
    pubyears = [str(y) for y in range(int(timezone.now().strftime("%Y")), 2015, -1)]
    context = {
        "country": country,
        "cumulative": {
            "publications_count": publications.count(),
            "authorships_count": authorships.count(),
            "authors_count": authorships.values_list("profile").distinct().count(),
        },
        "per_year": {},
    }
    for year in pubyears:
        authorships_year = authorships.filter(publication__publication_date__year=year)
        context["per_year"][year] = {
            "publications_count": publications.filter(
                publication_date__year=year
            ).count(),
            "authorships_count": authorships_year.count(),
            "authors_count": authorships_year.values_list("profile").distinct().count(),
        }
    return render(request, "stats/_hx_country_level_authorships.html", context)


@permission_required("scipost.can_view_statistics", raise_exception=True)
def statistics(
    request, journal_doi_label=None, volume_nr=None, issue_nr=None, year=None
):
    journals = Journal.objects.all()
    context = {
        "journals": journals,
    }
    if journal_doi_label:
        journal = get_object_or_404(Journal, doi_label=journal_doi_label)
        context["journal"] = journal
        if year:
            context["year"] = year
            context["citedby_impact_factor"] = journal.citedby_impact_factor(year)
            submissions = Submission.objects.filter(
                submitted_to__doi_label=journal_doi_label
            ).originally_submitted(
                datetime.date(int(year), 1, 1), datetime.date(int(year), 12, 31)
            )
            context["submissions"] = submissions
            nr_ref_inv = 0
            nr_acc = 0
            nr_dec = 0
            nr_pen = 0
            nr_rep_obt = 0
            nr_rep_obt_inv = 0
            nr_rep_obt_con = 0
            for submission in submissions:
                nr_ref_inv += submission.referee_invitations.count()
                nr_acc += submission.referee_invitations.accepted().count()
                nr_dec += submission.referee_invitations.declined().count()
                nr_pen += submission.referee_invitations.awaiting_response().count()
                nr_rep_obt += submission.reports.accepted().count()
                nr_rep_obt_inv += submission.reports.accepted().invited().count()
                nr_rep_obt_con += submission.reports.accepted().contributed().count()
            context["nr_ref_inv"] = nr_ref_inv
            context["nr_acc"] = nr_acc
            context["nr_dec"] = nr_dec
            context["nr_pen"] = nr_pen
            context["nr_rep_obt"] = nr_rep_obt
            context["nr_rep_obt_inv"] = nr_rep_obt_inv
            context["nr_rep_obt_con"] = nr_rep_obt_con
        if volume_nr:
            volume = get_object_or_404(Volume, in_journal=journal, number=volume_nr)
            context["volume"] = volume
            if issue_nr:
                issue = get_object_or_404(Issue, in_volume=volume, number=issue_nr)
                context["issue"] = issue
    return render(request, "stats/statistics.html", context)
