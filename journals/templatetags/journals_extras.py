__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from journals.helpers import paper_nr_string


register = template.Library()


@register.filter(name='paper_nr_string_filter')
def paper_nr_string_filter(nr):
    return paper_nr_string(nr)


@register.filter(name='latest_successful_crossref_deposit')
def latest_successful_crossref_deposit(publication):
    latest = publication.deposit_set.filter(
        deposit_successful=True).order_by('-deposition_date').first()
    if latest:
        return latest.deposition_date.strftime('%Y-%m-%d')
    else:
        return "No successful deposit found"


@register.filter(name='latest_successful_DOAJ_deposit')
def latest_successful_DOAJ_deposit(publication):
    latest = publication.doajdeposit_set.filter(
        deposit_successful=True).order_by('-deposition_date').first()
    if latest:
        return latest.deposition_date.strftime('%Y-%m-%d')
    else:
        return "No successful deposit found"


@register.filter(name='latest_successful_crossref_deposit_report')
def latest_successful_crossref_deposit_report(report):
    latest = report.genericdoideposit.filter(
        deposit_successful=True).order_by('-deposition_date').first()
    if latest:
        return latest.deposition_date.strftime('%Y-%m-%d')
    else:
        return "No successful deposit found"


@register.filter(name='latest_successful_crossref_deposit_comment')
def latest_successful_crossref_deposit_comment(comment):
    latest = comment.genericdoideposit.filter(
        deposit_successful=True).order_by('-deposition_date').first()
    if latest:
        return latest.deposition_date.strftime('%Y-%m-%d')
    else:
        return "No successful deposit found"


@register.filter(name='latest_successful_crossref_generic_deposit')
def latest_successful_crossref_generic_deposit(_object):
    latest = _object.genericdoideposit.filter(
        deposit_successful=True).order_by('-deposition_date').first()
    if latest:
        return latest.deposition_date.strftime('%Y-%m-%d')
    else:
        return "No successful deposit found"


@register.filter(name='pubfracs_fixed')
def pubfracs_fixed(publication):
    return publication.pubfractions_confirmed_by_authors and publication.pubfractions_sum_to_1
