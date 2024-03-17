__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Subsidy, PubFrac


"""
Allocate subsidy amount to compensations of PubFrac or coverage of expenditures.

Algorithm choices:
* [any_aff] Any PubFrac with affiliation to org
* [any_ctry] Any PubFrac with an affiliation in given list of countries
* [any_orgs] Any PubFrac with an affiliation in given list of orgs
  (helps handling interrelated orgs)
* [any_specs] Any PubFrac of publication in given list of specialties
* [all_fund] All PubFracs of publication acknowledging org in Funders
* [all ctry] All PubFracs of publications having at least one affiliation
  in given list of countries
* [all_spec] All PubFracs of publication in given list of specialties
* [all_aff] All PubFracs of publication with at least one author with affiliation to org

Our highest priority is for individual organizations to take responsibility
for their publishing, so the preferred algorithm is aff_org.

The algorithms are implemented in the following order,
(decreasing level of specificity):
* [any_aff]
* [any_ctry]
* [all_fund]
* [all_ctry]
* [all_spec]
* [all_aff]
"""


def allocate_to_any_aff(subsidy: Subsidy):
    """
    Allocate to PubFracs with affiliation to Subsidy-giver.
    """
    max_year = subsidy.date_until.year if subsidy.date_until else subsidy.date_from.year
    uncompensated_pubfracs = PubFrac.objects.filter(
        organization=subsidy.organization,
        publication__publication_date__year__gte=subsidy.date_from.year,
        publication__publication_date__year__lte=max_year,
        compensated_by__isnull=True,
    )
    for pubfrac in uncompensated_pubfracs.all():
        if pubfrac.cf_value <= subsidy.remainder:
            pubfrac.compensated_by = subsidy
            pubfrac.save()


def allocate_to_all_aff(subsidy: Subsidy):
    """
    Allocate to all PubFracs of Publications with at least one aff to Subsidy-giver.
    """
    max_year = subsidy.date_until.year if subsidy.date_until else subsidy.date_from.year
    uncompensated_pubfracs = PubFrac.objects.filter(
        organization=subsidy.organization,
        publication__publication_date__year__gte=subsidy.date_from.year,
        publication__publication_date__year__lte=max_year,
    )
    for pubfrac in uncompensated_pubfracs.all():
        # retrieve all uncompensated PubFracs for the relevant Publication
        pubfracs_for_pub = PubFrac.objects.filter(
            publication__doi_label=pubfrac.publication.doi_label,
            compensated_by__isnull=True,
        )
        for pf in pubfracs_for_pub.all():
            if pf.cf_value <= subsidy.remainder:
                pf.compensated_by = subsidy
                pf.save()
