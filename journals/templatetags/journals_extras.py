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
