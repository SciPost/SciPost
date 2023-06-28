__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class ForumsConfig(AppConfig):
    name = "forums"

    def ready(self):
        super().ready()

        from . import signals
        from forums.models import Post

        post_save.connect(
            signals.post_save_update_cfs_in_post_hierarchy,
            sender=Post,
        )
        post_delete.connect(
            signals.post_delete_update_cfs_in_post_hierarchy,
            sender=Post,
        )
