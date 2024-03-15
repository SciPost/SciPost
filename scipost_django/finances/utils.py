__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Subsidy, PubFrac, PubFracCompensation


def id_to_slug(id):
    return max(0, int(id) + 821)


def slug_to_id(slug):
    return max(0, int(slug) - 821)


def distribute_subsidy(subsidy: Subsidy, algorithm: str):
    """
    Allocate subsidy amount to compensations of PubFrac

    Algorithm choices:
    * any PubFrac ascribed to org from affiliations
    * full PEX of publication having at least one author affiliated to org
    * any PubFrac involving an affiliation with same country as org
    * full PEX of publication having at least one author affiliation with same country as org
    * full PEX of publication acknowledging org in Funders
    * full PEX of publication in specialties specified by Subsidy
    """

    algorithms = [
        "PubFrac_ascribed_to_Org",
        "full_PEX_if_author_affiliated_to_Org",
        "PubFrac_author_affiliation_same_country_as_Org",
        "full_PEX_author_affiliation_same_country_as_Org",
        "full_PEX_if_pub_funding_ack_includes_Org",
        "full_PEX_if_pub_matches_specialties",
    ]

    if algorithm is "PubFrac_ascribed_to_Org":
        max_year = (
            subsidy.date_until.year if subsidy.date_until else subsidy.date_from.year
        )
        pubfracs = PubFrac.objects.filter(
            organization=subsidy.organization,
            publication__publication_date__year__gte=subsidy.date_from.year,
            publication__publication_date__year__lte=max_year,
        )
        distributed = 0
        for pubfrac in pubfracs.all():
            print(f"{distributed = };\tadding {pubfrac = }")
            if pubfrac.cf_value <= subsidy.remainder:
                pfc, created = PubFracCompensation.objects.get_or_create(
                    subsidy=subsidy,
                    pubfrac=pubfrac,
                    amount=pubfrac.cf_value,
                )
                if created:
                    distributed += pubfrac.cf_value
            else:
                break
