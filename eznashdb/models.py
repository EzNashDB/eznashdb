import hashlib

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from eznashdb.enums import RelativeSize, SeeHearScore


class Shul(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shuls", null=True
    )
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=17)
    longitude = models.DecimalField(max_digits=22, decimal_places=17)
    place_id = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "shul"
        verbose_name_plural = "shuls"

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def display_lat(self):
        return self.rounded_lat + self.get_jitter("lat")

    @property
    def display_lon(self):
        return self.rounded_lon + self.get_jitter("lon")

    @property
    def rounded_lat(self):
        return self.round_coord(self.latitude)

    @property
    def rounded_lon(self):
        return self.round_coord(self.longitude)

    @staticmethod
    def round_coord(value):
        return float(round(value, 2))

    def get_jitter(self, coord_type):
        hash_input = f"{self.rounded_lat}_{self.rounded_lon}_{coord_type}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        return ((hash_value % 6000) - 3000) / 1000000


class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_rooms", null=True
    )
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    shul = models.ForeignKey("eznashdb.Shul", on_delete=models.PROTECT, related_name="rooms")
    name = models.CharField(max_length=50)
    relative_size = models.CharField(max_length=50, blank=True, choices=RelativeSize.choices, default="")
    see_hear_score = models.CharField(
        max_length=50, blank=True, choices=SeeHearScore.choices, default=""
    )

    class Meta:
        verbose_name = "room"
        verbose_name_plural = "rooms"

    def __str__(self) -> str:
        return f"{self.name}, {self.shul}"
