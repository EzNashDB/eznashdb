from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

from eznashdb.enums import KaddishAlone, RelativeSize, SeeHearScore


class Country(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=10)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "country"
        verbose_name_plural = "countries"

class Region(models.Model):
    id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey('eznashdb.Country', on_delete=models.PROTECT, related_name="regions")
    name = models.CharField(max_length=50)
    is_default_region = models.BooleanField(null=True, blank=True, default=False)

    def __str__(self) -> str:
        return f"{self.name}, {self.country.short_name}"

    class Meta:
        verbose_name = "region"
        verbose_name_plural = "regions"

class City(models.Model):
    id = models.BigAutoField(primary_key=True)
    region = models.ForeignKey('eznashdb.Region', on_delete=models.PROTECT, related_name="cities")
    name = models.CharField(max_length=50)
    latitude = models.CharField(max_length=50)
    longitude = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name}, {self.region}"

    class Meta:
        verbose_name = "city"
        verbose_name_plural = "cities"

class Shul(models.Model):
    id = models.BigAutoField(primary_key=True)
    city = models.ForeignKey('eznashdb.City', on_delete=models.PROTECT, related_name="shuls")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shuls")
    editted_by = ArrayField(models.IntegerField(), null=True, blank=True, default=list)
    name = models.CharField(max_length=50)
    has_female_leadership = models.BooleanField(null=True, blank=True)
    has_childcare = models.BooleanField(null=True, blank=True)
    has_kaddish_with_men = models.BooleanField(null=True, blank=True)
    enum_has_kaddish_alone = models.CharField(max_length=50, null=True, blank=True, choices=KaddishAlone.choices)


    def __str__(self) -> str:
        return f"{self.name}, {self.city}"

    class Meta:
        verbose_name = "shul"
        verbose_name_plural = "shuls"

class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    shul = models.ForeignKey('eznashdb.Shul', on_delete=models.PROTECT, related_name="rooms")
    name = models.CharField(max_length=50)
    relative_size = models.CharField(max_length=50, null=True, blank=True, choices=RelativeSize.choices)
    see_hear_score = models.IntegerField(null=True, blank=True, choices=SeeHearScore.choices)
    is_centered = models.BooleanField(blank=True, default=False)
    is_same_floor_side = models.BooleanField(blank=True, default=False)
    is_same_floor_back = models.BooleanField(blank=True, default=False)
    is_same_floor_elevated = models.BooleanField(blank=True, default=False)
    is_same_floor_level = models.BooleanField(blank=True, default=False)
    is_balcony_side = models.BooleanField( blank=True, default=False)
    is_balcony_back = models.BooleanField(blank=True, default=False)
    is_only_men = models.BooleanField(blank=True, default=False)
    is_mixed_seating = models.BooleanField(blank=True, default=False)
    is_wheelchair_accessible = models.BooleanField(blank=True, default=False)

    def __str__(self) -> str:
        return f"{self.name}, {self.shul}"

    class Meta:
        verbose_name = "room"
        verbose_name_plural = "rooms"
