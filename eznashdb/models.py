from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from eznashdb.enums import RelativeSize, SeeHearScore


class Shul(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_shuls"
    )
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    name = models.CharField(max_length=50)
    has_female_leadership = models.BooleanField(null=True, blank=True)
    has_childcare = models.BooleanField(null=True, blank=True)
    can_say_kaddish = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "shul"
        verbose_name_plural = "shuls"

    def __str__(self) -> str:
        return f"{self.name}"


class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_rooms"
    )
    updated_by = ArrayField(models.IntegerField(), blank=True, default=list)
    shul = models.ForeignKey("eznashdb.Shul", on_delete=models.PROTECT, related_name="rooms")
    name = models.CharField(max_length=50)
    relative_size = models.CharField(max_length=50, blank=True, choices=RelativeSize.choices, default="")
    see_hear_score = models.CharField(
        max_length=50, blank=True, choices=SeeHearScore.choices, default=""
    )
    is_same_height_side = models.BooleanField(blank=True, default=False)
    is_same_height_back = models.BooleanField(blank=True, default=False)
    is_elevated_side = models.BooleanField(blank=True, default=False)
    is_elevated_back = models.BooleanField(blank=True, default=False)
    is_balcony = models.BooleanField(blank=True, default=False)
    is_only_men = models.BooleanField(blank=True, default=False)
    is_mixed_seating = models.BooleanField(blank=True, default=False)
    is_wheelchair_accessible = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        verbose_name = "room"
        verbose_name_plural = "rooms"

    def __str__(self) -> str:
        return f"{self.name}, {self.shul}"

    def has_layout_data(self):
        return any(
            [
                self.is_same_height_side,
                self.is_same_height_back,
                self.is_elevated_side,
                self.is_elevated_back,
                self.is_balcony,
                self.is_only_men,
                self.is_mixed_seating,
            ]
        )
