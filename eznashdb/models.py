from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from eznashdb.enums import KaddishAlone, RelativeSize, SeeHearScore


class Shul(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shuls")
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    name = models.CharField(max_length=50)
    has_female_leadership = models.BooleanField(null=True, blank=True)
    has_childcare = models.BooleanField(null=True, blank=True)
    has_kaddish_with_men = models.BooleanField(null=True, blank=True)
    enum_has_kaddish_alone = models.CharField(
        max_length=50, null=True, blank=True, choices=KaddishAlone.choices)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "shul"
        verbose_name_plural = "shuls"


class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_rooms")
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    shul = models.ForeignKey(
        'eznashdb.Shul', on_delete=models.PROTECT, related_name="rooms")
    name = models.CharField(max_length=50)
    relative_size = models.CharField(
        max_length=50, null=True, blank=True, choices=RelativeSize.choices)
    see_hear_score = models.IntegerField(
        null=True, blank=True, choices=SeeHearScore.choices)
    is_centered = models.BooleanField(blank=True, default=False)
    is_same_floor_side = models.BooleanField(blank=True, default=False)
    is_same_floor_back = models.BooleanField(blank=True, default=False)
    is_same_floor_elevated = models.BooleanField(blank=True, default=False)
    is_same_floor_level = models.BooleanField(blank=True, default=False)
    is_balcony_side = models.BooleanField(blank=True, default=False)
    is_balcony_back = models.BooleanField(blank=True, default=False)
    is_only_men = models.BooleanField(blank=True, default=False)
    is_mixed_seating = models.BooleanField(blank=True, default=False)
    is_wheelchair_accessible = models.BooleanField(blank=True, default=False)

    def __str__(self) -> str:
        return f"{self.name}, {self.shul}"

    class Meta:
        verbose_name = "room"
        verbose_name_plural = "rooms"
