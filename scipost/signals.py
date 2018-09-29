__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import Profile

from .models import Contributor


@receiver(post_save, sender=Profile)
def link_created_profile_to_contributor(sender, instance, created, **kwargs):
    """
    When a new Profile is created, it is linked to the corresponding
    existing Contributor object.
    """
    if created:
        Contributor.objects.filter(user__email=instance.email).update(profile=instance)
