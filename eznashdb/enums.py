from django.db import models
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    S = ("S", _("S - Less than half"))
    M = ("M", _("M - Smaller, but at least half"))
    L = ("L", _("L - Same size or larger"))


class SeeHearScore(models.TextChoices):
    _1 = ("1", _("Very difficult"))
    _2 = ("2", _("Difficult"))
    _3 = ("3", _("Moderate"))
    _4 = ("4", _("Easy"))
    _5 = ("5", _("Very easy"))


class RoomLayoutType(models.TextChoices):
    is_same_height_side = ("is_same_height_side", _("Same height - Side"))
    is_same_height_back = ("is_same_height_back", _("Same height - Back"))
    is_elevated_side = ("is_elevated_side", _("Elevated - Side"))
    is_elevated_back = ("is_elevated_back", _("Elevated - Back"))
    is_balcony = ("is_balcony", _("Balcony"))
    is_only_men = ("is_only_men", _("Only Men"))
    is_mixed_seating = ("is_mixed_seating", _("Mixed Seating"))
