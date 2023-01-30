__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from forums.models import Post


@receiver(post_save, sender=Post)
def post_save_update_cfs_in_post_hierarchy(sender, instance, created, **kwargs):
    """
    When a Post is created, update all related Post (and Forum) calculated fields.
    """

    if created:
        if instance.parent:
            instance.parent.update_cfs()


@receiver(post_delete, sender=Post)
def post_delete_update_cfs_in_post_hierarchy(sender, instance, **kwargs):
    """
    When a Post is deleted, update all related Post (and Forum) calculated fields.
    """

    if instance.parent:
        instance.parent.update_cfs()
    # to cover multi-instance Post deletion in admin,
    # which might temporarily break recursive climbing of the hierarchy:
    if instance.anchor:
        instance.anchor.update_cfs()
