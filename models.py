from django.db import models
from django.core.urlresolvers import reverse

from staff.behaviors import WhiteLabelClientMixin, TimeStampedMixin

from .managers import LocationManager


class Location(WhiteLabelClientMixin):
    """
    Physical location to be related to WCLs.
    """
    code = models.CharField(max_length=64)
    client = models.ForeignKey('clients.Client', related_name='locations', blank=True, null=True)
    subtitle = models.CharField(max_length=128, blank=True)
    address = models.CharField(max_length=512)
    postal_code = models.CharField(max_length=512, blank=True)
    main_phone = models.CharField(max_length=32, blank=True)
    city = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)

    objects = LocationManager()

    class Meta:
        unique_together = ('white_label_client', 'code',)
        ordering = ('-code',)

    def __str__(self):
        return '%s, %s' % (self.address, self.city)

    def get_absolute_url(self):
        return reverse('locations:detailview', args=(self.code,))

    def get_edit_url(self):
        return reverse('locations:editview', args=(self.code,))


class GeoLocation(TimeStampedMixin):
    """
    Geocode which links `Location` objects to the 2D map.
    """
    location = models.OneToOneField('locations.Location')
    latitude = models.CharField(max_length=64)
    longitude = models.CharField(max_length=64)


class LocationObject(TimeStampedMixin):
    """
    An physical object can be assigned to a `Location` object.
    """
    location = models.ForeignKey('locations.Location', related_name='location_objects')
    code = models.CharField(max_length=64, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        _str = self.name
        if self.code:
            _str += ' (%s)' % self.code
        return _str
