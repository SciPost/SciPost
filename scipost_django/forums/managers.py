__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ForumQuerySet(models.QuerySet):
    def anchors(self):
        """Return only the Forums which do not have a parent."""
        return self.filter(parent_object_id__isnull=True)


class PostQuerySet(models.QuerySet):
    def anchors(self):
        """Return only the Posts which do not have a Post as a parent."""
        from django.contrib.contenttypes.models import ContentType

        type_forum = ContentType.objects.get_by_natural_key("forums", "forum")
        type_meeting = ContentType.objects.get_by_natural_key("forums", "meeting")
        return self.filter(parent_content_type__in=[type_forum, type_meeting])

    def motions_excluded(self):
        """Filter all Motions out of the Post queryset."""
        return self.filter(motion__isnull=True)
