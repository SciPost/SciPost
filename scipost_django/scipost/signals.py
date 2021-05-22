__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import Profile

from .models import Contributor


@receiver(post_save, sender=Profile)
def link_created_profile_to_contributor(sender, instance, created, **kwargs):
    """
    When a new Profile is created, it is linked to a corresponding
    existing Contributor object, provided it is unique (as defined by the name and email).
    If it is not unique, no action is taken.
    """
    if created:
        try:
            contributor = Contributor.objects.get(
                user__first_name=instance.first_name,
                user__last_name=instance.last_name,
                user__email=instance.email)
            contributor.profile = instance
            contributor.save()
        except Contributor.DoesNotExist:
            pass
        except Contributor.MultipleObjectsReturned:
            pass
