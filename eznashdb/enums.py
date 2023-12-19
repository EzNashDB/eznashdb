from django.db import models
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    S = ("S", _("S - Less than half"))
    M = ("M", _("M - Smaller, but at least half"))
    L = ("L", _("L - Same size or larger"))


class SeeHearScore(models.TextChoices):
    _1 = ("1", _("1 (Much more difficult than men's section)"))
    _2 = ("2", _("2"))
    _3 = ("3", _("3"))
    _4 = ("4", _("4"))
    _5 = ("5", _("5 (Equal to men's section)"))


class RoomLayoutType(models.TextChoices):
    is_same_height_side = ("is_same_height_side", _("Same height - Side"))
    is_same_height_back = ("is_same_height_back", _("Same height - Back"))
    is_elevated_side = ("is_elevated_side", _("Elevated - Side"))
    is_elevated_back = ("is_elevated_back", _("Elevated - Back"))
    is_balcony = ("is_balcony", _("Balcony"))
    is_only_men = ("is_only_men", _("Only Men"))
    is_mixed_seating = ("is_mixed_seating", _("Mixed Seating"))


class ChildcareProgramDuration(models.TextChoices):
    ALL = ("ALL", _("All of shacharit and mussaf on shabbat"))
    PART = ("PART", _("Part of shacharit and mussaf on shabbat"))
