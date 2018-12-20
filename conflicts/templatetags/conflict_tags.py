__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

register = template.Library()


# @register.filter
# def filter_for_contributor(qs, contributor):
#     """Filter ConflictGroup query for specific Contributor."""
#     # raise
#     return qs.filter(conflicts__origin=contributor).distinct()
