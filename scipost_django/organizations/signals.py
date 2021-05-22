__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver

from funders.models import Funder


@receiver(post_save, sender=Funder)
def funder_signal_update_org_nr_associated_publications(sender, instance, **kwargs):
    """
    If a Funder instance is saved, the associated Organization's calculated field
    cf_nr_associated_publications is recalculated.
    BEWARE: this updates the newly linked organization, but does not unlink the
    previous one if the organization is replaced (and not just added).
    The management command organizations:organization_update_cf_nr_associated_publications
    must thus be run regularly on the whole set of publications to ensure consistency.
    """
    if instance.organization:
        instance.organization.update_cf_nr_associated_publications()
