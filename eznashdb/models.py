from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from eznashdb.choices import ZERO_TO_EIGHTEEN
from eznashdb.constants import LAYOUT_FIELDS
from eznashdb.enums import ChildcareProgramDuration, RelativeSize, SeeHearScore


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
    latitude = models.CharField(max_length=255, blank=True)
    longitude = models.CharField(max_length=255, blank=True)
    place_id = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    has_female_leadership = models.BooleanField(null=True, blank=True)
    has_no_childcare = models.BooleanField(null=True, blank=True)
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
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_rooms", null=True
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
    is_wheelchair_accessible = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "room"
        verbose_name_plural = "rooms"

    def __str__(self) -> str:
        return f"{self.name}, {self.shul}"

    def has_layout_data(self):
        return any(getattr(self, field, False) for field in LAYOUT_FIELDS)


class ShulLink(models.Model):
    shul = models.ForeignKey("eznashdb.Shul", on_delete=models.PROTECT, related_name="links")
    link = models.CharField(max_length=255)

    class Meta:
        verbose_name = "link"
        verbose_name_plural = "links"

    def __str__(self) -> str:
        return f"{self.link}, {self.shul}"


class ChildcareProgram(models.Model):
    shul = models.ForeignKey(
        "eznashdb.Shul", on_delete=models.PROTECT, related_name="childcare_programs"
    )
    name = models.CharField(max_length=100)
    min_age = models.IntegerField(choices=ZERO_TO_EIGHTEEN, null=True, blank=True)
    max_age = models.IntegerField(choices=ZERO_TO_EIGHTEEN, null=True, blank=True)
    supervision_required = models.BooleanField(null=True, blank=True)
    duration = models.CharField(choices=ChildcareProgramDuration.choices, blank=True, max_length=20)

    class Meta:
        verbose_name = "childcare program"
        verbose_name_plural = "childcare programs"
        ordering = ["min_age", "max_age"]

    def __str__(self) -> str:
        return f"Childcare ({self.min_age}-{self.max_age}), {self.shul}"
