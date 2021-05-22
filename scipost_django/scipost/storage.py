__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.functional import cached_property


class SecureFileStorage(FileSystemStorage):
    """
    Inherit default FileStorage system to prevent files from being publicly accessible
    from a server location that is opened without this permission having been explicitly given.
    """
    @cached_property
    def location(self):
        """
        This method determines the storage location for a new file. To secure the file from
        'the public', we'll store it outside the publicly accessible MEDIA_ROOT folder.

        This also means you need to explicitly handle the file reading/opening!
        """
        if hasattr(settings, 'MEDIA_ROOT_SECURE'):
            return self._value_or_setting(self._location, settings.MEDIA_ROOT_SECURE)
        return super().location

    @cached_property
    def base_url(self):
        return settings.MEDIA_URL_SECURE
